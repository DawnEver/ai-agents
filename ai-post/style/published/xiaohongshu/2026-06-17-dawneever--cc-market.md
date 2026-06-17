---
platform: xiaohongshu
slug: dawneever--cc-market
published: 2026-06-17
title: 办公室改一半，回家 AI 还记得
---

# 办公室改一半，回家 AI 还记得

🔥 在办公室改了一下午的项目，回家 git clone 下来想接着干。结果 Claude Code 跟头一回见这项目似的——白天刚踩的坑、为啥用 pnpm、哪几个文件碰不得，全得我从头再讲一遍。讲到我自己都烦。

最近我写了个插件叫 rem，专门干一件事：把 AI 的记忆做成 markdown，直接提交进你的 git 仓库。

💡 这里先说清楚，Claude Code 自己是有记忆的，默认就开。

但它存在你这台机器的 `~/.claude` 目录里。我在办公室那台攒的记忆，回家这台根本看不到；团队里每个人也都各记各的，换台电脑就从零开始。

掏心掏肺跟它聊了一下午，回家换台机器它就把你忘得干干净净，那一刻真的有点想哭。😭

✨ rem 把记忆换了个地方放：不再锁在你电脑本地，而是变成 `.claude/memory/` 里一个个 markdown 文件，跟着仓库走。

于是我回家 git pull 一下，办公室那台攒的记忆原样回来；同事 clone 下来，也直接拿到所有踩坑记录。它还能在 PR 里 diff，团队一起看、一起改。

⚡ 更省心的是，它会自己打扫记忆。

短期记忆 90 天自动淘汰，常用的升级成长期留下来，索引只保留最近 20 条。不用建数据库、配向量库，就一堆纯文本，人能读、git 能存。

⭐ 有个细节我觉得特别妙。

记忆内容是要共享的，但「这条我点了几次、上次哪天碰的」这种状态是每台机器自己的事。rem 就把这俩拆开：内容进 git 跟着走，访问状态存在 gitignore 掉的小文件里，留在本地。所以两台电脑、两个同事，谁都不会去抢改对方的状态——当初分这两层，图的就是这个。

而且它从不真删东西，过期的记忆只标记成「丢弃」，文件还躺在那。哪天你想翻旧账，全都在。

👇 GitHub 搜 dawneever/cc-market，rem 这个插件就在里面，装上让你的 Claude Code 记忆跟着仓库走就行～想要直链评论区戳我。

或者直接把这两行丢给你的 Claude Code：

/plugin marketplace add DawnEver/cc-market
/plugin install rem@cc-market

#ClaudeCode #AI编程 #程序员必备 #开源工具 #效率提升

---

## 配图（单独上传，正文不内嵌 — 此清单不发）

1. **封面**（3:4）：![办公室改一半，回家接着改](../../images/xhs-cover-v2.png)
2. **配图**（3:4）：![原生记忆锁本地 vs rem 记忆随仓库走](../../images/native-vs-rem-3x4-v1.png)
3. **配图**（3:4）：![committed 的 .md 与 gitignored 的 _meta.json 分家](../../images/content-state-split-3x4-v1.png)
