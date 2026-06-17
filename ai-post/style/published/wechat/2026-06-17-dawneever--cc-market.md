---
platform: wechat
slug: dawneever--cc-market
published: 2026-06-17
title: 让 Claude Code 的记忆跟着仓库走：rem 的 committed-markdown 架构拆解
---

# 让 Claude Code 的记忆跟着仓库走：rem 的 committed-markdown 架构拆解


那天在办公室改到一半的项目，我回家想接着弄。git clone 下来，打开 Claude Code，准备接着上午的活干。

它问我：这个项目用的是哪个包管理器？

我愣了一下。就在几小时前，我们还为这件事在办公室争论了半天，最后定了 pnpm，我还顺手在一次会话里跟它解释了为什么不用 npm workspaces。那段推理，连同白天刚修过的那个诡异的 SSR 水合 bug、那个绝对不能动的鉴权中间件——全没了。不是它失忆，是那些记忆压根没跟着仓库过来。

这就是我想聊的痛点。

## 先把话说清楚：Claude Code 不是没记忆

得先纠正一个常见误会。很多人以为 Claude Code 啥都记不住——不对。从 v2.1.59 起，它自带了 auto memory，而且默认开着。Claude 会自己往一个 `MEMORY.md` 索引和若干主题文件里写它学到的东西，下次会话再读回来。

问题不在"有没有",在"存在哪儿"。翻一下官方文档，关键句子是这个：

> "Each project gets its own memory directory at `~/.claude/projects/<project>/memory/`... Auto memory is machine-local. Files are not shared across machines or cloud environments."

记忆是按你的 git 仓库路径来分目录的，但东西落在你**自己机器**的 home 目录下。所以我在办公室那台攒的记忆，回家 clone 一份代码根本带不过来；团队里每个人也都各记各的，换台电脑就从零开始；硬盘一抹，全没。它跟着你这台机器走，不跟着代码走。

这正是 GitHub 上两个 feature request 在求的东西。#38536 把它称作"团队采用的最大效率瓶颈"——一个人想明白了某件事，"那段推理只活在他自己的会话里，三个月后……上下文就没了"。#39195 则在抱怨没法按项目子集共享记忆，导致记忆要么过期要么噪音满天飞。


## rem 的核心思路：记忆就是提交进仓库的 markdown

rem 的解法朴素到有点反主流：既然记忆该跟着代码走，那就把它**提交进仓库**。

具体说，每条记忆是一个 markdown 文件，按日期嵌套着放在 `.claude/memory/YYYY/MM/DD/<slug>.md`。它进 git，跟着 clone 走，能在 PR 里被 diff、被 review。你同事拉一下分支，连带把"我们为什么用 pnpm"一起拉下来了。这就是我说的"记忆跟着仓库走"。

看一眼路径定义，`rem/lib.mjs:9-18`：

```javascript
export const repoRoot   = findProjectRoot();
export const memoryDir  = join(repoRoot, '.claude', 'memory');
export const rulesDir   = join(repoRoot, '.claude', 'rules');
export const indexFile  = join(rulesDir, 'MEMORY.md');
export const stateFile  = join(repoRoot, '.claude', '.rem-state.json');
```

注意 `memoryDir` 是从 `repoRoot` 算起的，不是从 home 算起的。一字之差，整个定位模型就反过来了：原生是"哪儿都在，但没法分享";rem 是"这个项目的记忆，跟代码一起做版本管理"。

市面上几乎所有记忆方案都往外走——mem0、Letta、官方的 memory MCP，无一例外把记忆塞进数据库或向量库。它们换来了语义检索，代价是丢掉了 git 版本管理、PR 可审、人类可读、零基础设施。有个 HN 老哥试了一二十个开源记忆项目后撂下一句话："还是没一个比我自己攒的那堆 markdown 文件更好用。"rem 干的，差不多就是把这句牢骚做成了工程。

## 三层模型：rules / long / short

记忆不能一股脑全往里堆，得有层次、有保鲜期。rem 分了三层。

最顶上是 **rules**（`.claude/rules/`，提交进仓库）——始终注入、永不淘汰。这是项目铁律，比如"鉴权中间件绝对不许碰"。

中间是 **long-term**（`tier:long`）——免疫那个 90 天的淘汰窗口，但不是终身制。下面会讲，它要是连着两个 prune 周期没人碰，照样往下降。

最底下是 **short-term**（`tier:short`，默认）——有时间边界，过期自动清。你随手记的临时上下文，大多落在这一层。

三层各管一摊：铁律永驻，重要的留着，零碎的自己会消失。

## 巧思一：内容和状态分家

这是我觉得整套设计里最聪明的一手，值得单独拎出来讲。

把记忆提交进 git，马上撞上一个现实问题：记忆文件里那些"上次访问时间""访问了几次"——这些状态是因人、因机而异的。我今天读了某条记忆，跟你读没读它，是两码事。要是把这些状态也写进提交的 `.md` 里，那每个人的访问记录都会改文件、都要 commit，多人协作立刻打架，git 历史被这种噪音淹掉。

rem 的处理是：内容和状态，分家。

提交进 git 的 `.md` 只装**知识本身**——这是要共享的。而那些易变的本地状态，单独放进一个 gitignored 的 `_meta.json` sidecar，每个日期目录一个。一个真实的例子，`rem/.claude/memory/2026/06/11/_meta.json`：

```json
{ "scope-isolation.md": { "accessed": "2026-06-11", "count": 1, "tier": "short" } }
```

`.gitignore` 里钉死了两条：`**/_meta.json` 和 `**/.claude/rules/MEMORY.md`。前者保证访问状态永远不进仓库，后者保证那个会重建的索引也不污染提交。

分家之后有个连带的好处：淘汰算法比的是**日期**，不是"谁什么时候摸过这个文件"。这一条很关键。短期记忆超过 90 天就算过期（`STALE_DAYS=90`），判据是 frontmatter 里的 `accessed` 日期——一个所有人看到的、确定的值，而不是某台机器上某个易变的触发时刻。于是两个人各自跑 prune，结论是一致的，谁也不会把对方的状态覆盖掉。


## 巧思二：让记忆自己保鲜

记忆放着不管会烂。原生 auto memory 没有按项目的淘汰和保鲜回路，rem 补上了这一环，而且是全自动的——靠两个钩子。

`rem/hooks/hooks.json` 挂了两个：

```json
{ "hooks": {
  "SessionStart": [{ "type":"command","command":"node \"${CLAUDE_PLUGIN_ROOT}/scripts/prune-memory.js\" --evict-stale","timeout":5 }],
  "Stop":         [{ "type":"command","command":"node \"${CLAUDE_PLUGIN_ROOT}/hooks/rem-hook.js\"","timeout":10 }] } }
```

每次会话一开始，`prune-memory.js` 就跑一轮整理：先做跨 scope 的完整性校验，然后干三件事——长期记忆要是上个 prune 周期没被碰过，降级成短期；短期超过 90 天，标记为 dropped；索引超过 20 条，从最老的短期记忆开始丢。完事更新 `lastPruneAt`，重建所有索引。一套降级、淘汰、控容量的组合拳，你什么都不用管。

升级则是反着来的。`bumpAccessed()` 在 `accessed` 推进到新的一天时给 `count` 加一（同一天反复读不算数，这个细节挺克制）。一旦 `access_count >= 3`，这条记忆就被提升成 `tier:long`——你反复用到的东西，系统当它是重要的，自动留下。

会话结束那头的 Stop 钩子，是个**触发闸门**，不是无脑触发。看 `rem-hook.js:9-11`：

```javascript
const MIN_STOP_COUNT = 3;
const MIN_SESSION_MS = 2*60*1000;
const MIN_SESSION_MS_SUBSTANTIVE = 30*1000;
```

得攒够 3 次 stop、会话年龄又超过 2 分钟（有实质改动的话放宽到 30 秒），才会触发 `/rem` 去总结这次会话学到的东西。它还会避让：要是有后台任务在跑，或者某个多轮技能把 `taskActiveUntil` 顶到了 30 分钟后，就放行停止、不打扰。免得你一个技能跑到一半，记忆总结突然插进来搅局。

## 不只是记忆：同一套存储还撑起了任务系统

聊到这儿，rem 已经是个挺完整的记忆方案了。但真正让我觉得它有想法的，是下一步：它把这套 git-tracked 的存储，复用成了别的东西的底座。

第一个是任务系统。`/todo` 这个命令背后是 `task-engine.js`，它干的事是直接去扫 `.claude/memory/`——找 sharp-review 留下的发现（`SR-*`）和手动建的任务（`MANUAL-*`）。注意，这里**没有一个派生出来的 `tasks.md`**。记忆条目本身就是任务的唯一真相来源。手动任务就是 markdown 里的勾选框：

```
- [ ] MANUAL-20260610-001 [MEDIUM] Fix login timeout (2026-06-10)
      module: auth
```

你 `/todo mark` 一下，`task-lib.mjs` 里的 `markFinding` 就去把对应文件里的 `- [ ]` 翻成 `- [x]`，或者改 sharp-review 文件里的 `**Status:**` 字段。任务状态，就这么活在记忆文件里，跟着仓库一起走、一起 diff。

第二个是代码锐评（sharp-review）。它是任务条目的主要生产者：评审跑完之后，`post-review.js` 把发现写进 `.claude/memory/YYYY/MM/DD/sharp-review.md`，带上 rem 的 frontmatter 和 `SR-YYYYMMDD-NNN` 这样的 ID，再调 `stamp-memory.js` 去建索引（`post-review.js:119-129`）。同一天重复评审，它会跟已有文件**合并**，把新来的 ID 重新编号避免撞车。


分工还划得很干净：sharp-review 自己管发现的全生命周期（写文件、盖索引，不甩给 task-engine），rem 管记忆索引、`/todo` 报告和状态更新。两个插件共用一份 `.rem-state.json`，靠 `shared/state.mjs` 里的 `deepMerge` 互相保留对方的 key，谁也不踩谁。

## 几个让我点头的工程细节

把这套东西真正做扎实，魔鬼全在细节里。挑几个我看了会心一笑的。

**永不删除，只标 dropped。** 文件从不被真删，prune 和 compact 只是在 `_meta.json` 里把它标成 `dropped`（见 `invariants.md`）。append-only 的好处是你有完整的审计轨迹，标错了还能捞回来。

**自愈式回填。** 万一有个 `.md` 在 `_meta.json` 里找不到对应记录（比如手动塞进来的），系统不报错，自动给它补一条默认值——`accessed` 取文件 mtime，`count:1`，`tier:short`（`lib.mjs:189-198`）。孤儿文件自己就被收编了。

**Windows / OneDrive 加固。** 这块是我自己拿真机踩出来的。我的工作目录就挂在 OneDrive 同步盘上，后台还有杀软盯着，文件写入偶尔就被锁住、直接报错。所以记忆和状态的写入我都做成先写 `.tmp` 再 rename 的原子操作，再加一次重试，专治这种 Windows 下的 flake；spawn 子进程也统一带上 `windowsHide:true`（commit `95d2a99` 就是为了堵这个）。

零运行时依赖，纯 Node ESM 加 markdown。一个解决"记忆该跟着代码走"的方案，本身就该是几个能被 review、能被 diff 的文本文件——它自己活成了它主张的样子。

## 快速上手

rem 是 cc-market 这个 Claude Code 插件套件里的一个。装好插件后，基本不用你操心——SessionStart 和 Stop 两个钩子会自动接管 prune 和总结。

你主要会用到这几个命令：

```bash
# 让 Claude 总结当前会话、更新记忆（通常由 Stop 钩子自动触发）
/rem

# 扫所有 scope，按模块汇总待办
/todo report

# 手动加一条任务
/todo add "修一下登录超时" --severity MEDIUM --module auth

# 标记状态
/todo mark MANUAL-20260610-001 fixed
```

第一次跑完，去翻一下 `.claude/memory/`，你会看到按日期码好的 markdown，每个都带 frontmatter。把它们 `git add` 进去、提交、推上去——下次你回家接着写也好，同事 clone 也好，这些记忆就跟着代码一起到位了。

想跑测试验证的话：

```bash
node --test cc-market/rem/tests/*.test.mjs
```

frontmatter、日期路径、记忆状态、scope 校验、钩子、迁移、任务库，覆盖得还挺全。

## 写在最后

绕了一圈，rem 真正的主张其实就一句：记忆应该是仓库里的一等公民，而不是某台机器 home 目录下的临时文件。

它没有语义检索，没有向量库，没有酷炫的 embedding。它只是把记忆做成了能提交、能 diff、能自动保鲜的 markdown，然后顺手用同一套存储撑起了任务系统和代码评审。这条路线放弃了一些东西，但换来的是 git 版本管理、PR 可审、人类可读、零基础设施——以及最朴素的那件事：在办公室改、回家接着改、换个同事接手，记忆都不丢。

代码在 GitHub，零依赖，连 Windows 下那行原子写的来历都写在 commit 里，你可以自己翻。

想装的话，把这两行丢给你的 Claude Code 就行：

```
/plugin marketplace add DawnEver/cc-market
/plugin install rem@cc-market
```

GitHub: https://github.com/dawneever/cc-market
