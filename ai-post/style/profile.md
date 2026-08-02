---
updated: 2026-08-02
articles: 12
---

## Openings I Use

### 小红书
- "🔥 平常写大型项目时候，我很想同时开三个 AI：Claude 定方案，复制到 DeepSeek 让它写，再贴回 Codex 让它挑刺。三个窗口来回横跳，复制粘贴复制粘贴，手都抽筋。"
- "🔥 用 Claude Code 的姐妹应该都有过这个纠结：想把思考档位 /effort 调低省点钱，手却不敢动——万一一切，之前缓存那一大坨全白烧，下一句还得重算，那不是更亏？"
- "🔥 想给乐器校个音，居然得先下App、注册、再看着手机内存被塞满——就为确认一下空弦准不准，这代价也太大了。所以我做了个网页，浏览器一开，对着乐器吹或弹就校音，一个App都不用下。"

### 微信公众号
- "前段时间我开发了一个 claude 插件叫 takeover，也发了两篇文章。但我用久了，还是不觉得够念头通达：每一次交接，都是一场失忆。"
- "我最近一直卡在一个特别小、特别烦的问题上：在 Claude Code 里切一下 `/effort`，我的 prompt 缓存到底会不会被清掉？"
- "要给吉他、钢琴、小提琴这些乐器校音，市面上的路数一般是：应用商店搜"调音器"，下载，注册，可能还要订阅。我只是想确认一下空弦准不准，却被要求先交一串个人信息。"

### 知乎
- "先给结论：切 `/effort` 不会清空 prompt 缓存，它是按 effort 分区。high、low 各占一套独立的缓存命名空间，在 TTL 内谁也不动谁。"
- "我先把结论放前面。如果你已经在 Claude Code 里干活，经常觉得'这个子任务换个模型会更好'，但又不想离开当前会话——那你要的大概率不是'把整个会话切到另一个模型'，而是'按任务把活派出去，还能记住上下文'。"
- "先讲我的场景。最近在玩布鲁斯口琴，每天从家走到实验室那十几分钟，路上正好练口琴——手头没有节拍器，就拿步伐当节拍器，一步一个四分音符。对新手来说，压音最难的其实是判断：仅凭耳朵，很难分辨压出来的音到底是'偏高/偏低'，还是'已经准确落在目标音上'。"

### Twitter/X
- "I switched Claude Code's /effort level mid-session and watched the prompt cache do something I didn't expect. It didn't reset — it partitioned. Each effort level quietly keeps its own cache namespace."
- "takeover v1 was a Bash heredoc. v2 was an MCP server. There's no v3 — it grew into something bigger with a new name: fabric. And the upgrade that actually matters: the models you hand work to now remember."
- "Tune any instrument in the browser — no app to download, nothing to install. Guitar, piano, violin, harmonica: open the link, grant the mic, play. That's it. I built Tone Chord Lab because your browser deserves a real tuner."

---

## Closings I Use

### 小红书
- "我想进化的不是代码，是人跟 AI 搭伙的方式：别再逼自己追上它的速度，让它学会替我省注意力。"
- "🙏 也说句老实话：我就在现在这个版本（cc 2.1.204）实测了一轮，不敢打包票往后版本永远这样。但至少当下，随便切。"
- "免费、开箱即用，音频全在本地、不上传，练琴隐私也握在自己手里。管你弹吉他还是吹口琴，快去试试。"

### 微信公众号
- "代码在 GitHub，三百行，零依赖，连 heredoc 那行的来历都写在 commit 里，你可以自己翻。"
- "结论回到最初那个问题：会动，但不是清空，是分区，切回去原样复活。而比这个结论更值钱的，是那条铁律——屏幕不作数，trace 才作数。"
- "这个工具最早只有一个朴素的想法：让"校音器只认单音、追不上压音"这两个老大难，变成能在浏览器里亲眼看见的东西。做成之后我发现，它顺手也把"识别和弦"这件校音器做不到的事做了。"

### 知乎
- "话说回来，如果你也在这些场景里，值得打开 https://tone.mingyangbao.site/ 试一下——浏览器一开就能校音，不用装 App。代码我放在 GitHub 上，算法层是零依赖的纯函数，直接 `node --test` 就能跑测试。"
- "但这篇我更想留下的是那套 harness。想量一个黑箱工具的运行时行为，与其对着 TUI 猜，不如让一个 Claude 去驱动另一个真实的 Claude，把每一个请求都摊在 API trace 上——证据分层、只在最顶层下结论。"
- "我回过头看，fabric 想做的其实就一件事：让'换个模型'从'要么切走整个会话、要么交接完就失忆'这两个都别扭的选项里跳出来——按任务派发，还记得住上文。你是不是需要它，取决于你桌上到底是一个脑子，还是一支队伍。"

### Twitter/X
- "The scarce resource was never how fast AI works. It's the one thing that doesn't parallelize — me. Stop optimizing throughput. Budget the human."
- "Open the live tool at https://tone.mingyangbao.site/ — and star it if it earns a spot in your pocket. ⭐"
- "takeover grew up: same seat, more models, now with memory. Star it if you want one terminal running the whole team. ⭐"

---

## Voice Markers

- "先说结论……完。" — 知乎开头直接给判断，结尾一字收束
- "复制粘贴税" / "记忆跟着仓库走" / "内容和状态，分家" — 自创概念词命名痛点或架构主张，压成一句可复述的锚点
- "我让贼来抓贼" / "商业互吹" — 用俗语和自造词点破"模型自审"的盲区与空洞（fabric 篇再次复用"让贼来抓贼"，已成招牌）
- "这道闸只管要不要打扰你，不管那件事还修不修" — 用生活化对比讲清技术边界，把架构决策翻译成直觉可感的承诺
- "加入光荣的进化吧" — slogan 双关收尾，从代码进化升维到人机协作方式进化
- "屏幕不作数，trace 才作数" — 自造铁律，把方法论压成可复述锚点（证据分三层，只认 API trace）
- "口琴是我的第一个用户，但不是唯一用户" — 把单一案例升维到通用（所有乐器），从个体痛点推及普适价值
- "一个终端指挥一支会记事的 AI 团队" / "你桌上到底是一个脑子，还是一支队伍" — 把多模型编排的价值压成一个可感画面
