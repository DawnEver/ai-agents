---
updated: 2026-07-08
articles: 11
---

## Openings I Use

### 小红书
- "🔥 平常写大型项目时候，我很想同时开三个 AI：Claude 定方案，复制到 DeepSeek 让它写，再贴回 Codex 让它挑刺。三个窗口来回横跳，复制粘贴复制粘贴，手都抽筋。"
- "🔥 用 Claude Code 的姐妹应该都有过这个纠结：想把思考档位 /effort 调低省点钱，手却不敢动——万一一切，之前缓存那一大坨全白烧，下一句还得重算，那不是更亏？"
- "🔥 同一个 AI 陪我写代码写久了，越看我的代码越顺眼，一条像样的意见都提不出来。"

### 微信公众号
- "前段时间我开发了一个 claude 插件叫 takeover，也发了两篇文章。但我用久了，还是不觉得够念头通达：每一次交接，都是一场失忆。"
- "我最近一直卡在一个特别小、特别烦的问题上：在 Claude Code 里切一下 `/effort`，我的 prompt 缓存到底会不会被清掉？"
- "写完一个功能，按下回车，Claude 顺手帮我 review 了一遍，三条建议，全是夸我的。我盯着那三条看了半天，心里只有一个念头：它在审自己刚写的代码，我让贼来抓贼。"

### 知乎
- "先给结论：切 `/effort` 不会清空 prompt 缓存，它是按 effort 分区。high、low 各占一套独立的缓存命名空间，在 TTL 内谁也不动谁。"
- "我先把结论放前面。如果你已经在 Claude Code 里干活，经常觉得'这个子任务换个模型会更好'，但又不想离开当前会话——那你要的大概率不是'把整个会话切到另一个模型'，而是'按任务把活派出去，还能记住上下文'。"
- "先说一个反直觉的结论：让几个 AI 审同一份代码，最有价值的不是它们都点头的地方，而是它们打架的地方——分歧处，往往就是真 bug 藏身的地方。"

### Twitter/X
- "I switched Claude Code's /effort level mid-session and watched the prompt cache do something I didn't expect. It didn't reset — it partitioned. Each effort level quietly keeps its own cache namespace."
- "takeover v1 was a Bash heredoc. v2 was an MCP server. There's no v3 — it grew into something bigger with a new name: fabric. And the upgrade that actually matters: the models you hand work to now remember."
- "A model reviewing its own code isn't a review. It can't catch what it couldn't catch the first time — same blind spots, same misses. The fix isn't a smarter model. It's a rival one."

---

## Closings I Use

### 小红书
- "我想进化的不是代码，是人跟 AI 搭伙的方式：别再逼自己追上它的速度，让它学会替我省注意力。"
- "🙏 也说句老实话：我就在现在这个版本（cc 2.1.204）实测了一轮，不敢打包票往后版本永远这样。但至少当下，随便切。"
- "像跟一个每天失忆的实习生共事，每次都得从头讲。现在换成了能持续来回的会话——我随口塞给 DeepSeek 一个暗号，聊到第五六轮回头再问，它居然还记得。"

### 微信公众号
- "代码在 GitHub，三百行，零依赖，连 heredoc 那行的来历都写在 commit 里，你可以自己翻。"
- "结论回到最初那个问题：会动，但不是清空，是分区，切回去原样复活。而比这个结论更值钱的，是那条铁律——屏幕不作数，trace 才作数。"
- "这次，它们会记事了。"

### 知乎
- "在这个并行 AI 时代，有个数字是任何 benchmark 都测不出来的——我这一天，到底被打扰了几次。"
- "但这篇我更想留下的是那套 harness。想量一个黑箱工具的运行时行为，与其对着 TUI 猜，不如让一个 Claude 去驱动另一个真实的 Claude，把每一个请求都摊在 API trace 上——证据分层、只在最顶层下结论。"
- "我回过头看，fabric 想做的其实就一件事：让'换个模型'从'要么切走整个会话、要么交接完就失忆'这两个都别扭的选项里跳出来——按任务派发，还记得住上文。你是不是需要它，取决于你桌上到底是一个脑子，还是一支队伍。"

### Twitter/X
- "The scarce resource was never how fast AI works. It's the one thing that doesn't parallelize — me. Stop optimizing throughput. Budget the human."
- "Stop guessing how Claude Code caches. Drive a real session and watch it. ⭐"
- "takeover grew up: same seat, more models, now with memory. Star it if you want one terminal running the whole team. ⭐"

---

## Voice Markers

- "先说结论……完。" — 知乎开头直接给判断，结尾一字收束
- "复制粘贴税" / "记忆跟着仓库走" / "内容和状态，分家" — 自创概念词命名痛点或架构主张，压成一句可复述的锚点
- "我让贼来抓贼" / "商业互吹" — 用俗语和自造词点破"模型自审"的盲区与空洞（fabric 篇再次复用"让贼来抓贼"，已成招牌）
- "这道闸只管要不要打扰你，不管那件事还修不修" — 用生活化对比讲清技术边界，把架构决策翻译成直觉可感的承诺
- "加入光荣的进化吧" — slogan 双关收尾，从代码进化升维到人机协作方式进化
- "屏幕不作数，trace 才作数" — 自造铁律，把方法论压成可复述锚点（证据分三层，只认 API trace）
- "服务器本身就是那个守护进程" — 一句话概括持久会话机制：不另起后台进程，服务活着会话就活着
- "一个终端指挥一支会记事的 AI 团队" / "你桌上到底是一个脑子，还是一支队伍" — 把多模型编排的价值压成一个可感画面
