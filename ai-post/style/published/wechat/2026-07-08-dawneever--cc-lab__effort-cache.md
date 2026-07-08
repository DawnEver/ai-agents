---
platform: wechat
slug: dawneever--cc-lab__effort-cache
published: 2026-07-08
title: 让一个 Claude 去盯另一个 Claude：我搭了套 harness，把 Claude Code 的缓存黑箱扒开了
---

# 让一个 Claude 去盯另一个 Claude：我搭了套 harness，把 Claude Code 的缓存黑箱扒开了

我最近一直卡在一个特别小、特别烦的问题上：在 Claude Code 里切一下 `/effort`，我的 prompt 缓存到底会不会被清掉？

这问题听着不起眼，但真要花钱的时候它就不小了。大量的历史对话和 Agent 自己的迭代内容，光让新会话读一遍就得几万 token。我下意识以为，既然还是同一个模型，切一下 thinking effort，顶多把这一次对话的 cache 重算一遍。可到底是不是这样，我心里没底——因为我压根看不到它真实发了什么。

我去搜了一圈，全网没人认真讲过这事。官方缓存文档只讲 breakpoint 和 TTL，没人真坐下来数过切 effort 前后的 token。

工具倒不是没有。`claude-tap` 就很好用——它是个装在本地的 MITM 代理，Claude Code 发往 Anthropic 的每一条 `/v1/messages` 请求和响应，它都能原样截下来落进一个 sqlite，请求体里的 `system`、`tools`、缓存计数全看得见。我只想瞄一眼某条请求的时候，它足够了。

但这类工具有个共性：**它们是给人看的**。我得自己坐在那儿，手动敲命令、手动截图、手动比对。我要的不是这个——我想让我的 Claude 自己迭代：自己设计实验、自己驱动一个真实会话跑完一整轮 high→low→high 的往返、自己把每条请求读回来下结论。于是我在 `claude-tap` 之上，搭了一套能自动驱动、又能逐请求留痕的 harness。

## 屏幕不作数，trace 才作数

先说清楚为什么这事没法靠"想"解决。

Claude Code 对我就是个黑箱。我在终端里输命令、切 effort，屏幕上滚过一堆漂亮的 TUI，可真正发给 API 的请求体长什么样——`system` 数组几个块、`tools` 带没带缓存断点、`usage` 里 `cache_read` 是多少——我一个字都看不到。

更麻烦的是 TUI 本身就不可信：它渲染的时候会把空格偷偷换成"光标右移"的转义序列，你 strip 完 ANSI 拿到的可能是 `Seteffortleveltolow` 这种连在一起的鬼东西，拿它当证据迟早翻车。所以我给自己定了条铁律：**屏幕不作数，trace 才作数。** 屏幕只用来找同步点，真正的判断全部去抓到的请求里读。想守住这条铁律，我得先有一双能插进 API 层的眼睛。

## 🔧 我的做法：让一个 Claude 驱动一个真实的 Claude Code

我搭的这套东西叫 cc-lab。它的核心思路有点套娃：**一个母 Claude，去驱动一个真实的、活的 Claude Code 子会话，同时把它发出的每一个 API 请求都截下来。**

不是模拟，不是打桩。是用 `node-pty` 起一个真的交互式 `claude` 进程，塞进一个隔离的 `CLAUDE_CONFIG_DIR`（免得污染我自己的配置），然后像人一样敲命令。我给这个 driver 只留了五个最小原语：

```js
// driver/driver.mjs — 一个薄薄的 PTY 封装，只暴露五个原语
await s.ready(60000);              // 清掉首次启动的信任/导入弹窗，等到输入框就绪
s.send('/effort');                // 往 TUI 打字
s.key('\x1b[C');                  // 发一个方向键（→，给 effort 滑块用）
await s.waitOutput(/apple/, 8000);// 等屏幕上出现某个 token 作同步点
await s.waitIdle(4000, 90000);    // 等它忙完这一轮
await s.close();                  // 收摊
```

trace 从哪来？就用前面说的 `claude-tap`，把每个 `/v1/messages` 的请求和响应原样落进 sqlite。每条记录里都躺着我想要的东西：请求体里的 `system`、`tools`、当前 effort 挡位，还有响应里的 `cache_read` 和 `cache_creation` 两个 token 计数。母 Claude 每跑一步就回来读一遍，一步都不靠猜。

## 岔开说说 fabric：我那套多模型底座

这里得先交代一个东西，不然后面接不上——fabric。

fabric 是我写的一个 Claude Code 插件（在 cc-market 里）。一句话概括，它把多家模型的调用编织进同一条工作流（名字取的就是"编织"的意思）：让你在**不离开 Claude Code** 的前提下，把活派给任意 provider 的模型——DeepSeek、Codex 都行——还能跟它们保持多轮会话。它是双形态的，既是一个能 `import` 的库，也是一个 MCP server。底层就一个 `call` 原语：叫一次是把活交接出去，叫 N 次就是编排一堆；再往上有 `spawn_session` 那套持久会话。整个引擎零依赖，纯 Node 内置库，装起来干净。

我在 cc-lab 里要借的，是 fabric 里一个不起眼的部件：**observe-proxy**。为什么要借它，下一节就会讲到。

## claude-tap 有个它看不见的死角

用着用着我碰到一个坎：`claude-tap` 靠改 `ANTHROPIC_BASE_URL` 来做中间人，可一旦我把某个 provider 路由到 Foundry（把 DeepSeek 这类 API 走 Foundry，是为了少踩最近 Claude Code 更新带来的缓存 miss），流量根本不走那个 base URL，`claude-tap` 就瞎了。

这正是我把 cc-lab 架在 fabric 上的原因。切到 `proxy` 这个观测档，子进程说的是最普通的 HTTP，对面是一个本地 observe-proxy，由它去持有真正的上游、鉴权和模型别名：

```js
const s = await launch({
  observe: 'proxy',        // 借 fabric 的 observe-proxy，而不是 claude-tap
  provider: 'deepseek',    // 连 tap 看不见的 DeepSeek 路由，这里也能截
});
// 抓下来的每一行落进 <runDir>/http.jsonl，用 fabric 的 observe-reader 读
```

说白了，一个 Foundry/DeepSeek 的 provider 之所以能被我看见，是因为我让 fabric 把子进程摁在本地代理前面只讲人话，上游那些脏活全交给代理扛。cc-lab 在这里，就是 fabric observe-proxy 的一个消费者兼验证器。

方法论上我也定了死规矩：证据分三层，只在结构化的那层上做断言。**API trace 可信度最高；** session 的 jsonl 状态次之；TTY 日志最低，只当输入通道和同步点用，绝不拿它下结论。

## ⚡ Round-trip：眼睛装好后，真相反转了

眼睛装好，我写了个 round-trip 的 case：一个会话里 high→low→high→low 走一圈，每一步都从抓到的请求里确认它当前真实的 effort 挡位，再对着 `usage` 数 token。

```js
await turn('apple');                             // T1 @ high（默认）→ 建 high 缓存
await setEffort('low');   await turn('banana');  // T2 @ low  → 另起一套 low 缓存
await setEffort('high');  await turn('cherry');  // T3 @ high → 切回来，还认不认 T1？
await setEffort('low');   await turn('date');    // T4 @ low  → 反方向，还认不认 T2？
```

trace 数出来是这样（Sonnet，同一会话）：

| 轮次 | 词 | effort | 切换 | cache_read | cache_create |
|------|-----|--------|--------|-----------|-------------|
| T1 | apple  | high | （默认）      | 50 626 | 9 730 |
| T2 | banana | low  | high→low      | 50 626 | 10 896 |
| T3 | cherry | high | low→high（升） | **60 356** | **1 355** |
| T4 | date   | low  | high→low      | 61 522 | **376** |

我盯着 create 那一列看：切到 low 时 T2 老老实实建了个 10 896 的 low 块（它读不到 high 那份），可一旦我切回 high，create 直接塌到 1 355。

真正的实锤在 T3 的 `cache_read`：它比 T2 高了差不多 **9 730**——恰好就是 T1 在 high 挡建出来的那个块。意思很清楚：我切回 high 那一下，T1 那个块**原封不动复活了**，根本没重建。T4 切回 low 同理，把 T2 的 low 块又捡了回来，只建了 376。

所以结论清楚了：切 effort 不是把缓存炸掉，是**按 effort 分区**——每个挡各留一套独立的缓存命名空间，TTL（约 1 小时）内切回去就命中，只有第一次踏进某个挡才冷 miss。

## 得交代的几个前提

这里我得把话说满。这套数据全部跑在 **cc 2.1.204** 上，是我一轮实测——我没敢把它当放之四海的定论。

另外有一个必须拎出来说的问题:表里那 5 万多 token 的跨会话前缀,之所以每次切换都稳稳命中,是因为我当天已经跑了几十轮,把 high、low 两档都预热过了,前缀本来就是热的，这个不能算切档位省出来的。
真正干净、能拿来下结论的,是同一会话里那块 session 专属缓存的复活——T1 在 high 建的 9,730,在 T3 切回来时原样被读回,`cache_create` 从 low 的 10,896 塌到 1,355。

落到实处：**effort 是一个缓存 key 的维度，不是一颗缓存炸弹。** 一小时之内 high、low 来回切，是便宜的；来回横跳也不会每次都把你几万 token 烧光。这个结论，我猜是猜不出来的，得靠那双插进 API 层的眼睛。

## Bonus：被两行路径浪费的 4000 token

cc-lab 配置好之后，我顺手还扒出来一件更气人的事。

Claude Code 的请求前缀里，有个约 4k token（15.8 KB）的指令块。我把它跨会话 diff 了一遍，122 行里**只有两行会变**：一行是当前工作目录，一行是带着 per-session UUID 的临时 scratchpad 路径。

坑就坑在，这两行正好卡在整个块的中间、在它唯一那个缓存断点**之前**。结果就是：那个 UUID 每个会话都换新的，一换就把它后面整整 4k token 的块全部作废，跨会话缓存一次都用不上。

在我看来这压根不是内容的问题，是**摆放位置的问题**。那 4k token 的指令内容其实一个字都不变，只要把这两行挪到消息层，或者挪到断点后面，整个 15.8 KB 的块立刻就能像 tools schema 一样跨会话复用了。每开一个新会话，白白省下约 4k token 的 `cache_create`。

这种东西，不搭 harness、不去 trace 里一行行 diff，你一辈子都不会知道它在漏钱。

## 收个尾

我最开始只是好奇切 effort 会不会动缓存，结果为了不猜，顺手搭出了一整套能盯着 Claude Code 看的 harness：cc-lab 用 PTY 开真实子会话、claude-tap 截包，底座是 fabric 的 session 原语和 observe-proxy，连 tap 看不见的 Foundry 路由都能看。

结论回到最初那个问题：会动，但不是清空，是分区，切回去原样复活。而比这个结论更值钱的，是那条铁律——屏幕不作数，trace 才作数。TUI 会把它想让你以为的样子渲染给你，只有 API trace 会告诉你它真正做了什么。

fabric（cc-market）的代码在 GitHub，observe-proxy、session 原语那一层你都能自己翻、自己接。cc-lab 这套 PTY 驱动的 harness 在这儿：https://github.com/DawnEver/ai-agents/tree/main/cc-lab 。想盯自己的 Claude Code 到底在往 API 发什么，把这双眼睛装上就行。

顺带说一句：你可能觉得这套 harness 太硬核。但它的底座 fabric 本身，是给普通用户用的——一行 `/plugin install fabric@cc-market`，就能在 Claude Code 里把活派给任何模型、还带多轮记忆，根本不用自己搭 harness。这篇是 fabric 被榨到极限的样子；想先上手 fabric 的话，我另有一篇专门讲它怎么用。

GitHub: https://github.com/DawnEver/cc-market
