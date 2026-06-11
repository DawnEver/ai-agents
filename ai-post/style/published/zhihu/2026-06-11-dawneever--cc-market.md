---
platform: zhihu
slug: dawneever--cc-market
published: 2026-06-11
title: takeover v2 技术拆解：从 Bash heredoc 到 MCP 服务器，一个多模型调度插件的架构升级
---

结论放前面：Takeover v2 解决了一个具体的问题——Workflow agent 不能跑 Bash，而 v1 的整个模型派发链路就建在 Bash heredoc 上。重写花了约 300 行，换来了一个真正的 MCP 原语：任何 MCP 消费者都能直接用 JSON-RPC 调三种外部模型。

## 为什么要重写

Takeover 是我日常最常用的 Claude Code 插件。v1 的设计很直接—— `/takeover:continue --provider deepseek "review this PR"`，takeover agent 把上下文打包，走 Bash heredoc 调 `companion.mjs`：

```bash
node companion.mjs <<'PROMPT'
<用户任务和上下文>
PROMPT
```

单引号 heredoc 不做变量展开，天然防 shell 注入——这个设计我当时是有意为之。但它只能在 Bash tool 里跑。Claude Code 更新 Workflow 功能后，我第一时间尝试把所有 skill 往 workflow 上迁移，Takeover 卡住了：Workflow agent 没有 Bash 权限，Codex 审阅者永远启动不了。

这不是加个 if-else 能绕过去的。调度层的入口不对，必须重写。

我选了 MCP stdio。HTTP server 要处理端口和防火墙，继续用 Bash 加 Workflow 绕路是打补丁。JSON-RPC over stdin/stdout 是 Claude Code 的原生插件协议——零网络开销，prompt 参数直接走 JSON params，shell 注入在架构层面消失。代价是从 96 行重写到约 300 行，换来了三个 MCP tool：`call_model`、`list_models`、`codex_status`。

## 四个架构决策

### 直连 Codex app-server，扔掉第三方插件依赖

v1 里，调 Codex 需要先装两个第三方插件：`openai/codex-plugin-cc` 跑代码审查，`codex-image@codex-image-in-cc` 调 gpt-image-2 生成图片。`findCodexCompanion()` 做的事就是翻别的插件的目录找入口文件——takeover 名义上是模型调度中间层，实际上底层 provider 的抽象是漏的。

v2 我写了一个 `CodexAppServerClient` 类，直接 spawn `codex app-server`，走 JSON-RPC 2.0。一个请求一个进程，没有 broker，没有 daemon。用完就关。这个类跟 takeover 的业务逻辑完全解耦——以后其他插件想跟 `codex app-server` 对话，可以直接 import。

```javascript
// CodexAppServerClient — 示意代码
export class CodexAppServerClient {
  async start() {
    const bin = this.codexPath || findCodexBinary(); // 查找 codex 可执行文件
    this.child = spawn(bin, ["app-server"], { stdio: ["pipe", "pipe", "pipe"] });
    return await this.send("initialize", {
      protocolVersion: "1.0",
      clientInfo: { name: "takeover", version: "2.3.5" },
    });
  }
  send(method, params) { /* Promise，收到 JSON-RPC response 时 resolve */ }
  onNotification(method, handler) { /* 路由 turn/completed, item/completed */ }
  async stop() { /* send shutdown → kill process */ }
}
```

图片生成和编辑也顺势接上了——`codex exec --full-auto` 调内置 imagegen skill 就是多一条 dispatch 路径的事。

### 五条 dispatch 分叉 + 确定性 flag 解析

v1 只有一条 task 路径。v2 拆成了五个：task（通用派发）、review（对抗审查）、agent（完整工具循环）、image-generate、image-edit。拆分标准很简单：如果两条路径的失败模式不同，就该拆开。task 超时应该 retry；review 超时意味着没拿到结构化输出，retry 没意义。

flag 解析也改了。v1 靠 agent 从用户输入里扒 `--provider` 和 `--model`。大多数时候没问题——直到有一次 agent 把 `--provider codex` 解析成了 `--provider claude`。Codex 审阅没跑成，半小时输出的是 Claude 的温和点评而不是对抗性审查。调了一下午。

v2 的解法是 `<command>` block：agent 只负责字符串包裹，flag 解析权交给 22 行解析函数：

```javascript
export function parseCommandBlock(prompt) {
  const re = /^\s*<command>\s*\n?(.*?)\n?\s*<\/command>\s*\n?/s;
  const match = prompt.match(re);
  if (!match) return { flags: {}, cleanPrompt: prompt };
  const cmdText = match[1].trim();
  const flags = {};
  const providerMatch = cmdText.match(/--provider\s+(\S+)/);
  if (providerMatch) flags.provider = providerMatch[1];
  const modelMatch = cmdText.match(/--model\s+(\S+)/);
  if (modelMatch) flags.model = modelMatch[1];
  if (cmdText.match(/--review/))      flags.mode = "review";
  if (cmdText.match(/--image-edit/))   flags.mode = "image-edit";
  else if (cmdText.match(/--image/))   flags.mode = "image-generate";
  return { flags, cleanPrompt: prompt.replace(re, "") };
}
```

正则不会把 `codex` 看成 `claude`。它没有"创造性"，而这恰好是解析命令行 flag 时需要的东西。review、image-generate、image-edit 三个模式我还加了硬 guard：代码层面强制要求 `--provider codex`，传 `--provider deepseek --review` 直接抛 Error，不是"建议不要这样做"。

### Agent 模式——给 DeepSeek 穿上外骨骼

引入 MCP 之后出现了一个新问题。v2 的 MCP server 走纯 JSON-RPC，DeepSeek API 我只能拿到一段文本输出——它能理解代码，但不能自己 Read 文件、不能跑 Bash、没有 agent loop。MCP 换来了 Workflow 兼容性，代价是把 DeepSeek 的手脚砍了。

`callAgentMode()` 是我的解法：spawn `claude -p`，启动前把环境变量换成 DeepSeek 的配置。Claude Code 的 agent loop 照常跑——Read、Write、Bash 全在——但 LLM 调用走 DeepSeek。Claude Code 出基础设施，DeepSeek 出脑子。

```javascript
export async function callAgentMode(provider, userPrompt, systemPrompt, model) {
  const env = loadProviderEnv(provider); // 清空 ANTHROPIC_* → 注入 provider env
  const child = spawn('claude', ['-p', fullPrompt], {
    env, stdio: ['ignore', 'pipe', 'pipe'], timeout: 300000,
    shell: process.platform === 'win32',
  });
  // 收集 stdout → 返回结果
}
```

两个配套细节是踩了坑才补上的。`loadProviderEnv()` 加载前先把所有 `ANTHROPIC_*` 环境变量删干净——第一版没做清理，本机 Claude API key 直接透传进了 DeepSeek 调用。`resolveModel()` 做 tier 名映射：用户写 `--model sonnet`，但 DeepSeek 只认 `deepseek-v4-flash`，第一次忘了映射直接 model not found。

## 横向对比

市面上做"MCP 多模型"的工具不少，但设计路线差异比我预想的大。

| 维度 | takeover v2 | Claude_MCP_Bridge | mcp-multi-model | deepseek-as-subagent |
|------|-------------|-------------------|-----------------|---------------------|
| 通信协议 | MCP JSON-RPC stdio | MCP + HTTP bridge | MCP (FastMCP) | MCP stdio |
| Codex 集成 | 直连 app-server JSON-RPC | 无 | 无 | 无 |
| 任务粒度 | 任务级（单条命令）| 会话/辩论级 | 查询级 | 子代理级 |
| 依赖复杂度 | 零 npm 依赖 | 需配多个 API key | 12+ provider | 需沙箱环境 |
| Agent 模式 | 借壳 claude -p | 无（纯 HTTP）| 无 | 独立子进程 tool loop |
| Flag 解析 | 确定性正则 | LLM 解析 | LLM 路由 | LLM 解析 |

三个关键差异。直连 Codex app-server 是 takeover v2 独有的——另外三个要么不支持 Codex，要么走第三方 CLI，拿不到 `review/start` 的结构化输出。Agent 模式让没有工具能力的模型借 Claude Code 的 harness 跑完整 agent loop。`<command>` block 的确定性解析不是多大的技术，但它把"LLM 该干什么、server 该干什么"的边界划清楚了——我认为这是最正确的设计决策。

## 不适合你的情况

v2 解决了我认为 v1 最致命的结构性缺陷，但几个先天限制没变。纯文本 API 不支持多模态，DeepSeek 这条线不识图。MCP server 单进程单线程，单次手递手够用，但想做全局任务调度器挂 MCP 后面，这个架构不合适。Agent 模式要求接收方是 Anthropic API 兼容的，纯 OpenAI 格式走不通。

v2 的定位没变：它还是"手递手"任务派发，不做 session 管理，不做 debating，不做 automatic routing。如果你想让 AI 自动判断"这个任务该派给谁"，需要的是 orchestration framework，不是 takeover。

回头看这四个决策——heredoc 换 MCP、直连 Codex 砍依赖、五条 dispatch 加确定性解析、给 DeepSeek 穿上外骨骼——有一个共同的逻辑：v1 证明了这件事有价值，v2 把每个卡点修到架构层面，而不是在表面贴胶带。

GitHub: https://github.com/DawnEver/cc-market

或者直接在 Claude Code 里：

```
/plugin marketplace add DawnEver/cc-market
/plugin install takeover@cc-market
```
