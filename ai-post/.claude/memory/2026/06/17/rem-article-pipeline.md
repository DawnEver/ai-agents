---
name: rem-article-pipeline
description: post-new run for the rem plugin article + wechat-writer agent-type registration gotcha
metadata:
  type: project
created: 2026-06-17
accessed: 2026-06-17
tier: short
access_count: 1
---

# rem 文章 pipeline 运行 (2026-06-17)

## 做了什么
跑 `/post-new dawneever--cc-market`，选题聚焦 **rem 插件**（不是 takeover，之前两篇 archived 都是 takeover）。
- Motivation：原生 auto memory 存机器本地 `~/.claude/projects/<project>/memory/`，不进仓库、换机/换同事就丢；rem 把记忆做成 committed `.claude/memory/*.md`，跟着 clone 走。
- 调研 + 四平台 v1 草稿 + 图片 manifest 全部完成，停在 step 08 user review。
- 角度：小红书情绪向(greenfield)、微信&知乎都技术深挖(知乎多一层路线横评)、Twitter EN+CN。

## Gotcha：wechat-writer agent 没注册
本次会话 spawn `subagent_type: wechat-writer` 报错 "Agent type not found"，可用列表只有 xiaohongshu-writer / zhihu-writer / twitter-writer，**唯独缺 wechat-writer**——尽管 `.claude/agents/wechat-writer.md` 文件存在且 frontmatter `name: wechat-writer` 正确。
- Workaround：spawn 通用 `claude` agent，让它先 Read `.claude/agents/wechat-writer.md` + `_writer-base.md` + `templates/wechat.md` 再按其工作流写稿，产出等价。
- 待查：为什么这个 agent 没被加载注册（其余三个都注册了）。可能 agent 注册器的某个解析/缓存问题。

## 准确性红线（写作时已守住，复用时记得）
- 别说 Claude Code "没有记忆"——原生 auto memory 存在、v2.1.59 起默认开；准确对比点是**存哪里、能否提交共享**。
- 不引用 claude-mem 的 star 数（来源争议 12.9k–65.8k）。
- 无已验证 Reddit/X 引用；可引用 GitHub #38536 / #39195、HN 46432004。

## 持久学习：persona 身份绑定（重要，已写进工作流）
"第一视角"一直被实现成**腔调**（说人话、用"我"），没绑定**身份**（"我"是谁）。研究笔记天生以外部审计第三方仓库口吻写，一引用代码细节，第三方"作者"就回流（"能看出作者真踩过坑""翻代码才看懂"）。修复：
- 新增 `style/private/author-identity.md`（gitignore：`.gitignore` 加 `style/private/`）——DawnEver/linxu/Mingyang/Mingyang Bao 名下仓库 ⇒ persona=author（我=作者本人）；不确定问用户。个人信息单独成文、默认不提交。
- `05-brief-gate.md` 新增 **Phase 0 身份确认**，写 `persona: author|deep-user` 进 brief；`_writing-craft.md` 加「身份绑定」小节 + banned-phrase「能看出作者…/翻代码才看懂」；`_writer-base.md` 写手强制读 persona。

## 持久学习：motivation 用"办公室→回家 git clone"
个人痛点场景 = 在实验室改一半的项目、回家 git clone 接着改（同一人两台机），**不是"买新电脑"**。团队场景才用"每个人各记各的、换台电脑从零开始"。

## 持久学习：三方会审必审 images（已加固工作流）
本轮漏了 image 审查 → 用户要求加固。`post-review/SKILL.md` Phase 6 标 MANDATORY + Hard Rule，`post-new/09-review.md` 图片审查升级为强制。**最常见漏点：标题/motivation 改后封面 hook 过时**（本篇小红书封面就是 v1 旧 hook，已改）。review-verdict.md 必须含 `## Image plan review` 段。

## 持久学习：post-review reviewer 配置
fork 已把 reviewer 池改为 Opus/DeepSeek/Codex，`pickStrategy: seed-mod` 每轮随机抽 2（不再固定 A/B）。本篇这轮用的是旧 Sonnet+DeepSeek 固定配置。
