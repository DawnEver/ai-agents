---
platform: wechat
slug: dawneever--cc-market__fabric
published: 2026-07-08
title: Claude 插件 takeover 长大了，现在叫 fabric：你的 Agent 团队会记事了
---

# Claude 插件 takeover 长大了，现在叫 fabric：你的 Agent 团队会记事了

## 交接一次，失忆一次

前段时间我开发了一个 claude 插件叫 takeover, 也发了两篇文章。

但我用久了，还是不觉得够念头通达：
每一次交接，都是一场失忆。你把活儿派出去，模型干完，漂亮。可你只要想接着聊下一句，就得把前因后果重新讲一遍。一次性的委托，就像抽奖——抽中了皆大欢喜，但如果想复盘上一把怎么中的，对不起，重开。

实在受不了了。所以我把它整个重做了，并改了个更加符合其实的名字，叫 fabric。

## 从 takeover 到 fabric

takeover 最早是一段 Bash heredoc（v1），后来长成一个 MCP server（v2，大概三百行），能直接调 Codex，有五种模式。用户是买账的，可我自己越用越别扭：我明明想让几个模型"一起"干活，它们之间却没有任何记忆。

我要的不是修修补补，是让它们真的一起干活。于是这一版我给它加了持久会话，让派出去的模型记得住上下文；又把原来分散的多家模型 provider、多种用法收敛成一个统一的调用入口。长到这一步，它做的早已不只是"把任务交接出去"，而是在编织多个模型的工作流——所以我给它改了名，叫 fabric，取的就是"编织"这层意思。

引擎从三百行长到了差不多两千行，但有一条我死守着：零依赖。整个 fabric 没有一个第三方 npm 包，全是 Node 自带的 `node:` 模块。你装它，不会顺带拖进来四十个你没听过的传递依赖。

## 核心升级：交接，从一次性变成持续协作 🚀

这一版我最想让你用上的，就一件事：**持续会话**。

以前的交接是"发一句、收一句、断线"。现在你可以用 `spawn_session` 开一个会话，让某个模型持续待在那儿，你一轮一轮跟它聊，它全程记得上下文。我把它从一张一次性抽奖券，做成了一个坐你旁边、有记忆的搭档。

它背后的实现，我用一句话概括给自己听：**服务器本身就是那个守护进程**。我没有单独起一个后台进程去管这些会话，而是让 MCP server 在进程内维护一张会话注册表——服务活着，会话就活着。少一个进程，少一处能崩的地方。

空口无凭。我当场做了个最土的测试：开一个子会话，告诉它"暗号是 Plumerge"，然后开下一轮，只问它暗号是什么。

```
> spawn_session(provider="deepseek")
  → session_id: sess_a1

> session_send(sess_a1, "记住，暗号是 Plumerge")
  → 好的，已记住。

> session_send(sess_a1, "暗号是什么？")
  → Plumerge
```

它答对了。就这么个土 demo，我盯着那行 Plumerge 看了半天——交接终于不再是一次性的了。

## 一个真实工作流：我怎么指挥这支团队 🔧

有了记忆，多模型协作才算真的立住。说说我自己每天怎么用它。

走量的粗活我丢给 DeepSeek。批量改样板、跑一堆机械的转换、翻译一大坨——这类不用多聪明、但要便宜要能扛量的活儿，它比 Opus 划算得多，一句 `call` 走 task 模式派过去就行：

```
call(provider="deepseek", mode="task",
     prompt="把这个目录下所有测试的断言，从 assert 风格批量改成 expect 风格")
```

审查和出图我交给 Codex。它的模型底子做代码不弱，更关键是换一双独立的眼睛——让写代码的那个模型审自己的代码，等于让贼来抓贼。PR 写完，我用 review 模式让 Codex 过一遍逻辑和安全；要配图，Codex 带原生的图像生成，image-generate 模式直接出——这也是我把它拉进来的一大理由。

而 Claude，我留着做总控。它拆任务、串流程、决定哪一步派给谁——我是导演，它是副导演，DeepSeek 和 Codex 是各有专长的演员。整条链路，我一次都不用离开当前这个终端。

说个我自己踩过、也顺手证明了这套 dogfooding 有用的坑：有阵子 Codex 的 call 返回值老是多带一截提示词回声，`<prompt echo>12` 这种，正确答案明明是 `12`。这 bug 是我用 fabric 调 fabric 的时候自己撞出来的，撞出来当场就修了。工具能审出自己的毛病，我才敢让你拿去审你的代码。

## 五种模式，一分钟看懂 💡

我给那个 call 留了五种模式，记住这五个词基本就会用了：

- **task** —— 派一个活，要个结果（走量的粗活给 DeepSeek 就走这个）
- **review** —— 让另一个模型审你的代码 / PR（交给 Codex）
- **agent** —— 让对方带着工具循环，自己干一段
- **image-generate** —— 从文字生图
- **image-edit** —— 改一张已有的图

再往上，持续会话那套是四个工具：`spawn_session` 开、`session_send` 聊、`list_sessions` 看开着哪些、`session_close` 关。加上 `list_providers`、`resolve_model`、`codex_status`，一共八个 MCP 工具——但我知道你日常真正天天用的，就 call 加 spawn_session 两个。

## 装它，一行命令 📌

如果你在用 Claude Code，我把安装做成了一句话：

```
/plugin install fabric@cc-market
```

装完你会多出那八个 MCP 工具。provider 这边我做得省心：claude 走原生 OAuth 不用配；codex 走它的 app-server，审查、出图、写文件都行；deepseek 走 API，在环境变量里填好 key 就能用。provider 列表是动态读的——你配了几家，它就认几家。

## 最后

takeover 这个名字我没舍得扔，它还活着——变成了 fabric 里那个 `fabric:takeover` 交接子代理，和 `/fabric:continue` 命令。从一段 heredoc，到今天你能在一个终端里指挥一支会记事的模型团队，这条线我走了三版。

还有一句得说：这篇讲的，其实是 fabric 最好上手的那一面——一行装、把活派出去、多轮记着。它能干的远不止这些。我最近那篇讲 Claude Code 缓存的文章，就是拿 fabric 的 observe-proxy 去扒运行时黑箱——让一个 Claude 驱动另一个真实的 Claude、逐请求截流量，算是把它榨到极限的一种进阶用法。你从这篇一行装入门，想看它能干多硬核的活，就去翻那篇。

代码在 GitHub，MIT，零依赖。GitHub 搜 DawnEver/cc-market，或者在 Claude Code 里直接 `/plugin install fabric@cc-market`，把你的模型团队接起来。

这次，它们会记事了。
