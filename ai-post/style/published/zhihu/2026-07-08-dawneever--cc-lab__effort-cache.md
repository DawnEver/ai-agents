---
platform: zhihu
slug: dawneever--cc-lab__effort-cache
published: 2026-07-08
title: Claude Code 切 /effort 会毁掉缓存吗?我搭了套 harness，把 Claude Code 的缓存黑箱扒开了
---

# Claude Code 切 /effort 会毁掉缓存吗?我搭了套 harness，把 Claude Code 的缓存黑箱扒开了

先给结论:切 `/effort` 不会清空 prompt 缓存,它是**按 effort 分区**。high、low 各占一套独立的缓存命名空间,在 TTL 内谁也不动谁。你从 high 切到 low 再切回来,之前那块 high 的缓存原样复活,几乎不用重建。

这个问题我一开始是纯好奇——切档位到底会不会把缓存打掉?翻了一圈,全网没有一篇文章讲过这件事。既然查不到,我干脆自己搭了套 harness ,把 Claude Code 真实发出去的每一个请求扒下来看。这篇讲的其实是那套 harness :怎么搭、凭什么信它的数据,以及它扒出来的这个分区结论到底靠不靠谱。

## 想量缓存,第一道坎是你根本看不见它发了什么

对我来说,Claude Code 是个黑箱。你在终端里敲 `/effort high`,它背后到底往 API 塞了什么、缓存字段怎么变,TUI 一个字都不会告诉你。我想回答"切档位动不动缓存",靠猜没用,得看它真实的 `/v1/messages` 请求体和响应里的 `cache_creation_input_tokens`、`cache_read_input_tokens`。

问题是,怎么稳定地拿到这些数据。我不想每次手动敲命令、手动截图——那样既不可复现,也没法自动跑一整轮 high→low→high 的往返。所以我要的不是一次性抓包,而是一套能**驱动真实会话**、又能**逐请求留痕**的观测系统。

## harness 长什么样:一个父 Claude 驱动真实的 Claude Code

我搭的东西叫 cc-lab,核心思路是让一个父 Claude 通过 PTY 去开一个**真实的**交互式 `claude` 子进程,像人一样往里打字、切档位、发消息。

它用 `node-pty` 拉起子进程,给驱动层封了几个原语:`send`(发文本)、`key`(按键)、`waitOutput`/`waitIdle`(等它稳定下来)、`ready`、`close`。每一轮跑之前,我都给它开一个全新隔离的 `CLAUDE_CONFIG_DIR`,避免上一轮的状态污染这一轮。

这里有个我一开始就定死的原则:**TUI 只是输入通道,断言永远不落在屏幕上**。终端里刷出来的字符可以用来判断"它是不是准备好接收下一条了",但绝不能拿屏幕上的数字当证据——那是被渲染过、被截断过的二手信息。真正作数的东西,得从抓包里拿。

## 凭什么信这些数:证据分三层,只在最顶层下结论

抓包这块,我用 `claude-tap` 做 MITM,把每一个 `/v1/messages` 的请求和响应原样落进 sqlite。但光有抓包还不够,我给整套观测定了个证据分层,优先级从高到低:

- **API trace(权威层)**:真实请求体 + 响应里的缓存计数,唯一能下结论的证据。
- **session jsonl(状态层)**:Claude Code 自己写的会话状态,可以交叉印证,但它是派生数据。
- **TTY log(参考层)**:屏幕日志,只用来判断时序,**永不 assert**。

这个分层不是洁癖。同一个数字,屏幕上显示的、jsonl 里记的、和 API 真实发出去的,三者可能对不上——被渲染逻辑改过、被本地状态缓存过。谁离线最近,谁的可信度就最低。所以我的规矩很简单:凡是要写进结论的数字,必须能在 API trace 里指到那一条原始请求。

还有个不容易注意的坑，卡了我好久:如果你的流量走的不是 Anthropic 直连,而是被路由到 Foundry 或 DeepSeek,`claude-tap` 这种贴着 Anthropic 端点的抓包**根本看不见**。为此我把 fabric 的 observe-proxy 接了进来。fabric 是我写的一个多模型编排插件(在公开的 cc-market 里):让你不离开 Claude Code 就能把任务派给任意 provider 的模型、还能和它们保持多轮会话,其中就带一个能把子进程流量镜像到本地的 observe-proxy。cc-lab 在 proxy 模式下直接复用 fabric 那套代理启动和子进程环境构造的逻辑,让子进程改说普通 HTTP、把上游交给这个本地代理来持有。这样一来,原本对抓包不可见的 Foundry/DeepSeek 路由流量,也进了同一张观测网。cc-lab 在这里就是 fabric observe-proxy 的一个消费方和验证方。

## 分区结论是怎么读出来的:看往返,不看单点

有了harness ,我跑了一轮 Sonnet 上的 effort 往返:high → low → high → low,每一步都盯着 `cache_create` 和 `cache_read` 的变化。（测试环境:cc 2.1.204。）

| 轮次 | effort | 切换 | cache_read | cache_create | 读到了什么 |
|------|--------|------|-----------|--------------|-----------|
| T1 | high | (默认) | 50,626 | 9,730 | 首次进 high,建了一块 high 缓存 |
| T2 | low | high→low | 50,626 | 10,896 | 切到 low,没复用 high,另起一套自己的 |
| T3 | high | low→high | 60,356 | 1,355 | 切回 high,`cache_read` 比 T2 多了约 9,730——正是 T1 那块 |
| T4 | low | high→low | 61,522 | 376 | 再切回 low,又把 T2 的 low 块捡回来了 |

关键在 T3。如果切档位真的会**全局清空**缓存,那每次切回 high 都得把 T1 那块重新建一遍,`cache_create` 应该又是一万多。但它只建了 1,355,而 `cache_read` 精确地多出了约 9,730——正是 T1 在 high 挡建的那块,一个字不差地被读回来。T4 再切回 low 也一样:只建了 376,把 T2 的 low 块又捡了回来。

我据此判断:high 那块缓存从头到尾没被删,只是在我切到 low 时被"停到"它自己的命名空间里等着。**effort 不是一颗清缓存的炸弹,它是缓存 key 的一个隐藏维度。**

## 横向对比:观测 Claude Code 运行时,有哪些路子

我搭这套之前也想过省事的办法。把几种观测方式摆一起对比更清楚:

| 维度 | cc-lab + fabric | 单用 claude-tap | 读 session jsonl | 手动屏幕抓取 |
|------|-----------------|-----------------|------------------|--------------|
| 断言依据 | API trace(权威) | API trace(权威) | 派生状态 | 屏幕像素(最弱) |
| 看得见 Foundry/DeepSeek 流量 | ✅ 经 observe-proxy | ❌ 只见 Anthropic 直连 | 部分 | ❌ |
| 驱动真实会话、可复现 | ✅ PTY 自动跑往返 | ❌ 只抓包不驱动 | ❌ | ❌ 全手动 |
| 环境隔离 | ✅ 每轮全新 config dir | 需自己搭 | — | 易串味 |
| 适用场景 | 系统性量运行时行为 | 快速瞄一眼直连请求 | 事后翻会话状态 | 演示、非严谨观察 |

结论其实很直白:如果你只想瞄一眼直连请求,`claude-tap` 单独用就够了,轻。但一旦你要跑往返实验、要覆盖非直连路由、要保证下次还能复现同一条曲线,就得有人来驱动会话、来隔离环境、来把不可见的流量拉进观测网——这正是我把 PTY 驱动和 fabric observe-proxy 缝在一起的原因。

## 得交代的几个前提

这一轮数据跑在 cc 2.1.204 上,是一次实测,我没敢当成放之四海的定论。

另外有一个必须拎出来说的问题:表里那 5 万多 token 的跨会话前缀,之所以每次切换都稳稳命中,是因为我当天已经跑了几十轮,把 high、low 两档都预热过了,前缀本来就是热的，这个不能算切档位省出来的。
真正干净、能拿来下结论的,是同一会话里那块 session 专属缓存的复活——T1 在 high 建的 9,730,在 T3 切回来时原样被读回,`cache_create` 从 low 的 10,896 塌到 1,355。

**一个附带发现**。我还顺手扒到一块 ~4k token(15.8 KB)的指令块,每个 session 都被挤出缓存——罪魁只有两行:cwd 路径和一个 per-session 的 scratchpad UUID,它俩正好压在这块唯一断点的前面。这是**放置 bug,不是内容 bug**:把这两行挪到 message 层,整块就能跨会话缓存。这个我暂时只是记下,还没做完整验证。

## 回到最初那个问题

绕了一圈,最初的好奇有答案了:切 `/effort` 确实动缓存,但动的方式不是清空,而是**按档位分区、切回来复活**。实际结论对省 token 很友好——在 TTL(约 1 小时)内来回切档位是便宜的,effort 是一个缓存 key,不是一颗缓存炸弹。

但这篇我更想留下的是那套 harness 。想量一个黑箱工具的运行时行为,与其对着 TUI 猜,不如让一个 Claude 去驱动另一个真实的 Claude,把每一个请求都摊在 API trace 上——证据分层、只在最顶层下结论,剩下的交给数据。这套分层,也是我敢不被屏幕上的表象带偏、只认 trace 的底气。

补一句:这套观测台偏硬核,但它依赖的 fabric 本身对小白很友好——一行 `/plugin install fabric@cc-market`,就能在 Claude Code 里把任务派给任意模型、还带多轮会话,根本不必自己搭harness 。我另有一篇专门讲 fabric 的上手,从那篇入门、顺着这篇深挖正好。

fabric(observe-proxy 那部分)在公开的 cc-market 里:GitHub 搜 `DawnEver/cc-market`。cc-lab 这套 PTY+tap 的观测台在这儿:https://github.com/DawnEver/ai-agents/tree/main/cc-lab 。如果你也在跟 Claude Code 的缓存和成本较劲,这套思路值得借。
