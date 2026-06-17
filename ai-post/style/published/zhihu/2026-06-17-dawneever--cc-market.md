---
platform: zhihu
slug: dawneever--cc-market
published: 2026-06-17
title: rem 技术拆解：把 Claude 的记忆做成可提交、可 diff、自动淘汰的 markdown
---

# rem 技术拆解：把 Claude 的记忆做成可提交、可 diff、自动淘汰的 markdown


先说结论：如果你的痛点是"团队里每个人的 Claude Code 各记各的、换台电脑就从零开始"，那 rem 这条路线值得看一眼。它把记忆做成提交进 git 仓库的 markdown，跟着 clone 走、能在 PR 里 review。但它没有语义检索、需要人工策展，如果你要的是"塞一个向量库自动召回历史会话"，那它不是你要的东西。下面把取舍讲清楚。

## 原生记忆不是没有，是"留不住"

先纠正一个常见误解：Claude Code 不是没有记忆。从 v2.1.59 起，auto memory 默认就是开的，Claude 会自己往里写。问题出在它存在哪。

按官方文档，auto memory 落在 `~/.claude/projects/<project>/memory/`——你 home 目录下，机器本地。它按仓库路径分目录，但文件本身在你这台机器上。结果就是：我在办公室那台机器上跟 Claude 喂熟的上下文，回家 clone 一份代码接着改，它一点都带不过来；同事 clone 一份，同样拿不到；团队里每个人各记各的，换台电脑就从零开始；重装系统，全没了。

这不是我一个人的体感。GitHub 上有两个专门的 feature request 在求这件事——#38536 直接把它称作"团队采用的最大效率瓶颈"，原话是"那些推理只活在他个人的 session 里，三个月后上下文就没了"；#39195 抱怨"没法在一组项目之间共享记忆"。HN 上也有人试了十几个记忆类项目后撂下一句："到现在没有哪个比我自己维护一堆 markdown 文件更好用"（46432004）。


## 三条路线，我把取舍摆出来

记忆"留不住"这个问题，市面上的解法其实分成三派，各有各的代价。

第一派是原生的机器本地 memory，刚才说了——零配置、always there，但不进仓库、不可共享。

第二派是外置到数据库或向量库，这是绝大多数"记忆插件"的做法。mem0 用 LLM 抽事实再塞进向量/图谱检索；官方的 memory MCP 是知识图谱；claude-mem 这类则是 hook 抓会话、AI 压缩成观察条目，落 SQLite + 向量。这一派换来了语义检索——你能"模糊召回"相关历史。代价是记忆变成了数据库里一坨不可读的状态，丢了 git 版本化、丢了 PR 可审、丢了人能直接读懂的纯文本，还得维护一份额外的基础设施。

第三派是把记忆当成仓库内的 committed markdown，rem 走的就是这条。说实话这条路上人不多。我查下来，basic-memory 算是唯一另一个 markdown 路线的，但它又在 markdown 之上叠了 SQLite + 向量索引和个人知识库那套，本质上半只脚还是踩在第二派。

所以这三条路线的核心张力，其实是同一个：你想要语义检索的"聪明"，还是想要纯文本的"可控、可读、可共享"。把它做成表更清楚：


| 维度 | rem（仓库内 markdown） | 原生 auto memory | 外置向量库（mem0/claude-mem/memory MCP） |
|------|------|------|------|
| 存储位置 | `.claude/memory/`，仓库内提交 | `~/.claude/`，机器本地 | 外部 DB / 向量 / 服务 |
| 跟随 clone | 是 | 否 | 否 |
| 团队共享 | 走 git，零额外设施 | 每人每机各一份 | 需共享服务/账号 |
| PR 可审 / 可 diff | 是，就是纯文本 | 否 | 否，DB 状态不可读 |
| 语义检索 | 无 | 无 | 有（这是它最大优势） |
| 淘汰机制 | 自动：90 天淘汰 + 长期降级 | 索引截断在 200 行/25KB | 各家不一 |
| 额外依赖 | 零（纯 Node + markdown） | 零 | 数据库/向量库/MCP 服务 |

一句话：rem 不跟第二派比"聪明"，它比的是"这份记忆能不能像代码一样被团队管理"。

## 它到底是怎么存的

把路线讲完，再看 rem 的实现，会发现它的巧思都长在"内容可共享、状态不可共享"这条分界线上。

记忆文件落在 `<repo>/.claude/memory/YYYY/MM/DD/<slug>.md`，按日期嵌套、append-only、提交进 git（`rem/lib.mjs:9-18`）。每个文件带一段 frontmatter，记 `tier`、`created`、`accessed`、`access_count`（`memory-conventions.md:18-34`）。

关键在于，那些"易变的"状态——某条记忆最近被碰是哪天、被碰了几次——不写进提交的 md，而是单独放进 gitignored 的 `_meta.json` sidecar，每个日期目录一份。真实长这样（`rem/.claude/memory/2026/06/11/_meta.json`）：

```json
{ "scope-isolation.md": { "accessed": "2026-06-11", "count": 1, "tier": "short" } }
```

这个内容/状态分离是我觉得最聪明的一笔。如果把"访问次数"也提交进仓库，两个人同时用就会在这个计数上打架——你 +1、我 +1，commit 历史里全是"把 count 从 3 改成 4"这种没人想看的 diff。分离之后，提交的 md 是纯知识、人人一致；易变状态留在本地，淘汰时比较的是"日期"而不是"谁碰得多"。`.gitignore` 里硬性挡掉 `**/_meta.json` 和 `**/.claude/rules/MEMORY.md`。

记忆分三层（`prune-memory.js`、`memory-conventions.md:10-16`）：**rules** 永不淘汰、每次注入；**long** 免疫 90 天窗口；**short** 默认层、有时效。淘汰发生在 SessionStart——挂在 hook 上自动跑（`rem/hooks/hooks.json`）：long 层若两个 prune 周期没被碰就降级，short 层超 90 天标记 dropped，索引超过 20 条就先丢最旧的 short。注意是"标记 dropped"不是删——文件永远不物理删除（`invariants.md`），留审计、可恢复。升级反过来：同一条记忆被访问到 `access_count>=3`，自动升 long。


还有个细节挺能体现工程成色：孤立的 md 文件（有内容、没 sidecar 记录）会自动 backfill 成 `accessed:mtime, count:1, tier:short`（`lib.mjs:189-198`），不会因为缺状态就崩。Windows/OneDrive 上还做了原子写 + 重试、`windowsHide:true` 防黑窗弹（commit 95d2a99）——这点我自己在 OneDrive 同步目录里踩过坑：文件刚写一半就被同步进程锁住，报错弹一脸，知道有多烦。

## 记忆不只是"回忆"，它是个底座

到这里 rem 还只是个"更好的记忆"。真正让我觉得它路线想得远的，是它把这份 git-tracked 存储复用成了别的东西的底座。

`/todo` 任务系统就建在上面。它没有单独的 `tasks.md` 派生文件，task-engine 直接扫 `.claude/memory/` 里的条目当数据源（`rem/skills/todo/SKILL.md:7-8`、`task-engine.js:87-99`）——记忆条目本身就是任务的 source of truth。手动任务是 frontmatter + checkbox 行，`MANUAL-YYYYMMDD-NNN` 这样带日期的 ID，排序天然按时间。

sharp-review（同套件里的代码审查插件）也往同一个存储里写。它跑完审查后，把发现以 `SR-YYYYMMDD-NNN` 写进 `.claude/memory/.../sharp-review.md`，再 stamp 进索引（`post-review.js:108-129`）。当天重复审查会 merge 进已有文件、给新 ID 重新编号防撞。多个插件共享一份 `.rem-state.json`，靠 `deepMerge` 保留各家不认识的 key、互不覆盖（`shared/state.mjs:34-40`）。

这就是"记忆即平台"的意思：审查发现、待办任务、会话学习，三样东西落在同一份随仓库走的 markdown 里。换个工具、换个插件，这份资产还在。

## 谁该用，谁别碰

讲了这么多优点，得把局限也摆平，不然就成软文了。

适合你的情况：你在做团队协作的项目，希望"为什么这么改"的推理能跟着代码进 PR、被 review、被新同事 clone 到；你受够了机器本地记忆换机就丢；你想要零额外基础设施（rem 是纯 Node + markdown，零运行时依赖）。这几条命中，它很顺手。

不适合你的情况，我也直说三条。第一，它**没有语义检索**——你不能"模糊召回"一段相关历史，只能靠那份不超过 20 条的索引和人去翻。要语义召回，老老实实上 mem0 那一派。第二，它**需要人工策展**——committed markdown 的代价就是得有人决定什么值得记、定期清理，它不会替你判断信息价值。第三，那个 **20 条索引上限**——超了自动丢最旧的 short 层，长期跑的大项目得接受"索引只留近期热点"这个设定，全量靠翻 git 历史。

所以它不是"更强的记忆"，是"另一种记忆"——拿语义检索换可读、可审、可共享。这个交换值不值，取决于你更怕"记不全"还是更怕"管不住"。我自己是后者，所以这条路线对我成立。

项目地址：https://github.com/dawneever/cc-market（`rem` 插件）。如果你也在折腾 Claude Code 的团队记忆，值得 clone 下来读读 `lib.mjs`，那个 `_meta.json` 分离的设计单看代码就挺有意思。

想直接装的话，把这两行交给 Claude Code：

```
/plugin marketplace add DawnEver/cc-market
/plugin install rem@cc-market
```
