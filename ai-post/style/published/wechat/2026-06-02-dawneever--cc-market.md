---
platform: wechat
slug: dawneever--cc-market
published: 2026-06-02
title: 不再被单个模型卡住：用 takeover 在 Claude Code 里玩转多模型编排
---

# 不再被单个模型卡住：用 takeover 在 Claude Code 里玩转多模型编排

我的工作流很简单：Claude Code 负责复杂推理和 plan，便宜量大的 DeepSeek 负责实现，Codex 来锐评和做有难度的修改。

但这个工作流还有个绕不开的卡点：Chrome MCP 远端控制目前只支持 Claude 订阅。可 Claude 的额度大家都知道，几分钟就没了。

每次想把一个具体任务交给另一个模型，都得打开一个全新的 Claude Code 窗口，把当前的代码、CLAUDE.md 里的项目约定、任务背景，一段一段复制过去。等它跑完，再复制回来。来回切了五六次，等我把结果贴回原来的会话，已经忘了自己原本要干嘛了。

所以现在的问题根本不是"哪个模型更强"。而是我每次想借另一个模型的脑子，都得交一笔**复制粘贴税**——丢掉上下文，丢掉手头的文件状态，丢掉正在进行的任务。

这笔税，我交了半年多。

## 大家都在解决错误的问题

我去翻了一圈现有方案，发现一个有意思的事。

知乎上"DeepSeek 做 Claude Code 后端"的教程能堆成山，deepclaude 在 Hacker News 上拿了 432 分。但它们干的是同一件事：**会话级替换**——在你启动 Claude Code 之前，改个环境变量，把整个底层模型换成 DeepSeek。

这就好比，你嫌一个员工不会算账，于是把整个公司的人全开了，重新招一批会算账的。可你想要的从来不是"换一批人"，你想要的是**一个会算账的、一个会写代码的、一个会规划的，同时归你指挥**。

这中间隔着一个以前很少有人关注的概念，可以叫做**奴隶主视角**：你不切换身份，你坐在 Claude 这把椅子上当包工头，把具体的活派给最合适的那个工人，干完了结果直接回到你手里。

takeover 这个插件，干的就是这件事。

## 关于 takeover

这个插件目前托管在我自己创建的 cc-market 这个社区插件市场里， 刚打 v1.0.0 tag。

所谓社区插件市场，其实就是一个github 仓库 https://github.com/DawnEver/cc-market ，可以让 AI 帮你安装。

这个插件的核心代码也只有三百行出头，没有 npm 依赖，纯用 Node.js 内置模块撸出来的。

它不替换你的 Claude，不抢你的会话，只做一件事：**让你在当前会话里，把任意一个任务甩给 DeepSeek、Codex，或者任何 Anthropic 兼容的模型，然后把结果接回来。**


## 三个我天天在用的场景

说原理太空，我直接讲我现在每天怎么用它分工。


### 场景一：实现和审查交给 DeepSeek

一般来说 deepseek-v4-pro 可以实现 sonnet 同等的任务，但 deepseek 的性价比高得离谱。
所以一个很爽的工作流就是，让 Claude 做完 plan，然后把具体实现甩给 DeepSeek，让它当主力干活的那个。
又比如 PR 写完了，再让它过一遍挑安全问题和逻辑 bug：

```bash
/takeover:continue --provider deepseek "review this PR for security issues and logic bugs"
```

它会把当前会话的上下文打包，交给 DeepSeek，结果直接返回给 Claude Code。

### 场景二：有难度的修改和锐评交给 Codex

最让我上头的一个场景就是让 Codex 锐评代码，一针见血，它还能带 `--write` 直接动手改文件——Claude 这条路走不通的活，Codex 接过来了：

```bash
/takeover:continue --provider codex --write "rename all snake_case functions to camelCase in src/"
```

当然这里也要感谢 Codex plugin for Claude Code(https://github.com/openai/codex-plugin-cc)

## 真正聪明的地方：那行 heredoc

讲到这，我得说一个藏在代码里、但我觉得最值得拎出来的设计。

你想，takeover 要把你的 prompt 传给底层脚本去调模型。最偷懒的写法，是把 prompt 直接拼进命令行参数里。但你的 prompt 里要是带了反引号、`$()`、分号呢？那就是教科书级别的 shell 注入——你以为在问问题，实际上在执行命令。

我用 heredoc 把这个口子焊死了：

```bash
node companion.mjs <<'PROMPT'
review this PR for security issues
PROMPT
```

关键是那个加了单引号的 `<<'PROMPT'`。单引号意味着里面的内容**完全不做变量展开**——你写什么就是什么，反引号也好、`$HOME` 也好，全当普通文本。prompt 从 stdin 进去，压根不碰命令行参数。

更让我服气的是这行代码的来历。它是在一次 Codex 代码审查指出 shell 注入风险**之后**专门补上的。

换句话说，我自己也在用多模型编排——让 Codex 审了自己的代码，然后照着改了。这本身就是这个插件最好的广告。


## 保姆级上手

说了这么多，装起来其实没几步。

第一步，在 Claude Code 里装插件（来自我自己的 cc-market 市场）：

```bash
/plugin marketplace add https://github.com/openai/codex-plugin-cc
/plugin install takeover
```

第二步，配模型。takeover 读的是 `~/.claude/claude_env_settings.json`。加一个 DeepSeek 的条目，因为它是 Anthropic 兼容 API，填进去就能用：

```json
{
  "providers": {
    "deepseek": {
      "base_url": "https://api.deepseek.com/anthropic",
      "api_key": "sk-你的key",
      "model": "deepseek-v4-pro"
    }
  }
}
```

`claude` 和 `codex` 这俩是内置的，被特殊处理成原生路径，根本不用写进配置文件——零配置开箱即用。Codex 要先跑一遍 `/codex:setup` 授权。

这里预告一下, 在我的工作流里  `claude_env_settings.json` 不仅仅用于 takeover，我的 claude code 本身也支持基于这个文件快速切换模型提供商。敬请期待我接下来的 claude code 配置分享的文章。

第三步，确认它认得你的工人。这条命令会动态列出你配好的所有 provider：

```bash
/takeover:models
```

看到 deepseek、codex 都在列表里，就齐活了。

## 几个我踩过的坑，先告诉你

公平起见，也说说边界。

takeover 走的是纯文本 API，**DeepSeek 这条路不识图**——你想让它看截图、看 UI，没戏，那活还得 Claude 自己来。单次调用上限 16000 token，做代码审查、PR 分析、规划够用，但别指望它一口气读完整个仓库。

另外它给 Codex 留了 600 秒超时（普通 API 调用是 300 秒），因为 agent loop 跑起来确实慢。第一次用的时候别以为卡死了，它只是在埋头干活。

## 写在最后

我用了半年多 Claude Code，最大的转变不是某个模型变强了，而是我终于不用在"选哪个模型"这道单选题上纠结了。

Claude 统筹、DeepSeek 实现、Codex 锐评动手——坐在一把椅子上，不丢上下文，不交复制粘贴税。这种当奴隶主的感觉，用过就回不去了。

代码在 GitHub，三百行，零依赖，连 heredoc 那行的来历都写在 commit 里，你可以自己翻。

GitHub: https://github.com/DawnEver/cc-market