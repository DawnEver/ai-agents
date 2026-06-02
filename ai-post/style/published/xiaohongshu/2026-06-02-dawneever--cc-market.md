---
platform: xiaohongshu
slug: dawneever--cc-market
published: 2026-06-02
title: 开源工具 #程序员必备 #ClaudeCode #DeepSeek #效率提升
---

🔥 自从给 Claude Code 装了这个插件，我在终端里同时使唤三个 AI 给我打工，上头到停不下来。

🚀 我写了个叫 takeover 的 Claude Code 插件（cc-market 里第一个），核心就一句话：一条命令，把当前这个任务甩给 DeepSeek、Codex 或任何 Anthropic 兼容的模型去干，结果直接回到我现在的会话里。

💡 起因很具体：我想要在我的工作流里实现让 Claude 模型拿来做复杂推理和 plan，便宜量大的 DeepSeek 拿来实现，再让 Codex 来锐评一遍。
当然， Claude Code 使用中还有别的卡点，比如我很喜欢的 Chrome MCP 和远端控制——这玩意儿目前只支持 Claude 订阅，可 Claude 的额度众所周知，几分钟就没了。每次想换个模型接手，都意味着——重开一个标签页、把 CLAUDE.md 和上下文整段复制过去、等、再复制回来。那一刻我是真嫌弃自己，活像个人肉剪贴板。


✨ 装上之后整个心态就变了。Claude 居中调度，做计划，做那些只有订阅才能跑的事；DeepSeek 便宜量大干脏活累活，实现交给它，性价比拉满；Codex 负责锐评和有难度的修改，带 `--write` 👨‍💻 它能真的动手改文件——这是 Claude 这条路走不通的活。我全程没离开过当前会话，CLAUDE.md、打开的文件、任务状态全在。

🎯 整个插件 300 行核心代码，零 npm 依赖，纯 Node 内置模块。DeepSeek 配个 key、Codex 走 `/codex:setup`，剩下的就是开始当老板了。

👇 GitHub 搜 DawnEver/cc-market，takeover 就在里面，把连接交给你的 claude code 就行。想要直链评论区戳我～

#开源工具 #程序员必备 #ClaudeCode #DeepSeek #效率提升