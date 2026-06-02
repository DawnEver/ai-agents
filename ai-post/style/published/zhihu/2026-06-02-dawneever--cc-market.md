---
platform: zhihu
slug: dawneever--cc-market
published: 2026-06-02
title: 为什么我开始觉得一个模型不够用
---

先说结论：如果你已经在用 Claude Code，又时不时觉得"这个活让别的模型干会更好"，那我做的这个插件 takeover 值得装。它不替换 Claude，也不要你切会话。它只做一件事——让你在当前这个 Claude 会话里，把某一个具体任务甩给 DeepSeek 或 Codex，干完把结果送回来。一条命令，不切标签页。

## 为什么我开始觉得一个模型不够用

我对 Claude Code 没什么不满，它的工具调用和 agent 循环是我用过最顺的。但用久了，盲区也很清楚。

具体卡点有两个。第一，我的工作流是 Claude 做 plan，deepseek-v4-pro 做实现（和 sonnet 能力接近，性价比好很多），Codex 来锐评和改文件。第二，Chrome MCP 远端控制目前只支持 Claude 订阅，可 Claude 额度几分钟就没了，得临时把任务交给别的模型顶上。

问题是每次切换都得开一个全新的 Claude Code 窗口、把 CLAUDE.md 上下文和任务状态全部重新喂一遍——喂完拿到答案，再复制回来。这个来回的复制粘贴税，我交了很多次。

后来我想明白了：我要的不是"换一个更好的模型"，而是"让每个模型干它最擅长的活，而我坐在指挥位上"。Claude 负责拆任务、调工具、管文件；推理密集的扔给 DeepSeek；要真正落地改文件的，交给 Codex。takeover v1.0.0 就是为这个心智模型写的。


## 所以我写了 takeover

所以我写了 takeover 这个插件，核心三个命令：`/takeover:continue`、`/takeover:plan`、`/takeover:models`。

整个核心逻辑就 300 行左右，零 npm 依赖，纯 Node.js 内置模块。它读 `~/.claude/claude_env_settings.json` 里的配置，然后分三条路派发：Anthropic 兼容的 API（DeepSeek 走这条）、原生 `claude -p`、以及 codex。

## 横向对比：它和现有方案到底差在哪

这是我觉得最该讲清楚的部分。市面上"Claude + DeepSeek"的方案不少，但绝大多数解决的是另一个问题。

| 维度 | takeover | deepclaude | openclaude | CC Switch |
|------|----------|------------|------------|-----------|
| 切换粒度 | 任务级（会话内单条命令） | 全局模型重定向 | 整个会话换 provider | 会话级一键切换 |
| 是否保留 Claude | 是，Claude 仍是主控 | 否，底层模型被换掉 | 否，整会话换人 | 否 |
| 上下文连续性 | 不丢，留在原会话 | 重定向后语境随之改变 | 切换即重开 | 切换即重开 |
| 能否多模型同存 | 能，一会话内调多个 | 不能，单一后端 | 不能 | 不能 |
| 依赖 | 零 npm 依赖 | 需配置代理层 | 需配置 | 工具型 |
| 让 Codex 改文件 | 支持 `--write` | 不涉及 | 不涉及 | 不涉及 |

差别其实就一句话：那几个方案都是"会话开始时决定用哪个模型"，而 takeover 是"会话进行中，临时把某一个任务派给某一个模型"。前者是换人，后者是分工。

deepclaude 在 HN 拿了 432 分，证明大家确实想要 Claude 的工具能力配 DeepSeek 的推理。但它的做法是把 Claude 的底层模型整个换成 DeepSeek——你得到的是"披着 Claude Code 壳的 DeepSeek"，agent 循环还是 Claude 的，但每次推理都走 DeepSeek。这在成本上很香（DeepSeek 大约便宜 7 倍），可你失去了选择权：不是每个任务都该让 DeepSeek 来。takeover 反过来，默认还是 Claude，只在我点名的那一刻才借别人的脑子。

所以如果你的诉求是"我就想全程用便宜的 DeepSeek 后端"，deepclaude 或 openclaude 更直接，takeover 反而绕。但如果你想要的是"大部分时间 Claude，关键时刻精准调用别的模型"，那目前我没找到第二个做任务级派发的。

## 用了这段时间，说几个真实的地方


最实用的场景是代码审查。我写完一个 PR，顺手 `/takeover:continue --provider deepseek "review this PR for security issues"`，DeepSeek 的结果直接流回当前会话，我接着让 Claude 根据建议改。整个过程没离开过 Claude Code。

有个工程细节我自己挺满意：prompt 是通过 heredoc `<<'PROMPT'` 传给子进程的，单引号包住、不做变量展开。这不是我一开始就想到的，是某次 Codex 帮我 review 代码时点出了 shell 注入的风险，我才专门加上的。算是多模型分工的一个小彩蛋——连这个插件本身的安全设计，都是另一个模型帮忙把的关。

API 调用那条路还加了重试：遇到 429/502/503/504 会做两次指数退避。超时方面 API 是 300 秒，Codex 因为 agent 循环更长给到 600 秒，单次最多 16000 token，做 code review 和方案规划够用。企业用户如果开了 `CLAUDE_CODE_USE_FOUNDRY=1`，会切到 Foundry 的企业 base URL，不用改一行代码。

## 哪些情况我不建议你装

它不是万能的，有几个边界我得说清楚。

第一，它是纯文本 API 派发。DeepSeek 这条链路不识图，你要做截图分析、UI 走查这类多模态的活，派给它没用，还是得 Claude 自己来。

第二，如果你压根不用 Claude Code，这插件对你没意义——它的前提就是 Claude 当主控。想全程用 DeepSeek 当后端省钱的，前面说了，deepclaude 更对路。

第三，它现在 star 还是 0，v1.0.0 刚打的 tag。测试覆盖我写了 20 多个断言，包括"prompt 不出现在进程参数里"这条安全不变量，但毕竟是新东西，生产环境上你自己掂量。配置上也有门槛：DeepSeek 要自己填 API key，Codex 要先跑 `/codex:setup`，不是装上就能用。

说到底，多模型分工有没有用，取决于你是不是真的遇到过"这个活该换个模型"的时刻。如果你遇到过，而且已经在用 Claude Code，那装一个试试，反正零依赖、免费。

GitHub：https://github.com/DawnEver/cc-market