---
platform: xiaohongshu
slug: dawneever--cc-market
published: 2026-06-11
title: Takeover v2 升级，我在 Claude 里当包工头
---

Takeover v2 升级，我在 Claude 里当包工头
🔥 Takeover v1 那版"在 Claude 里同时使唤三个 AI 打工"已经够上头了—— 最近我又迭代更新好几轮， takeover 终于升级到 v2 了。

这次更新不是修修补补，我直接重写了调度层。

更新的契机是 Claude code 最近更新了 workflow 功能，可以用js 脚本把工作流固化下来。我收到更新的第一时间就尝试把我的所有 skill 和 插件升级为 workflow,这时候问题出现了。
Takeover v1 靠 Bash heredoc 给外模型传指令，可是这种方式只能在 Skill 里触发。Workflow agent 想帮忙派活？它没 Bash 权限。
v2 换成 MCP JSON-RPC 服务器，任何 agent、Workflow、甚至别的 MCP 插件，都能直接调外模型干活。

当然，引入 MCP 也带来一个问题，就是没法进入 agent 模式了，所以我又专门添加了 agent 模式，通过 claude -p 加上不同环境变量配置不同的模型提供商。

第二大更新是 takeover 不再依赖其他 Codex 插件实现了 review 和 图片生成的功能。
Takeover v1 时候，让 Codex 审查代码还得先装 `openai/codex-plugin-cc`，
想要调用 gpt-image2 还需要 先装 codex-image-in-cc

这不仅仅让人有种寄人篱下的感觉，而且多个插件之间的管理很混乱，
takeover 是成为了一个中间层，但是又并没有完全抽象和隐藏掉底层模型 provider，让强迫症很不爽 。

于是在 v2 版本里，我自己写了个 `CodexAppServerClient` 类，直接跟 `codex app-server` 走 JSON-RPC 协议——握手、通知路由、生命周期全管了。
顺便解锁了锐评、图片生成、图片编辑三种新模式。

👇 GitHub 搜 DawnEver/cc-market，takeover 就在里面。链接交给你的 Claude Code 就行。
/plugin marketplace add DawnEver/cc-market
/plugin install takeover@cc-market
#claude  #开源工具合集  #AI效率  #程序员日常  #deepseek #人工智能 #开发
