---
updated: 2026-06-19
articles: 9
---

## Openings I Use

### 小红书
- "🔥 同一个 AI 陪我写代码写久了，越看我的代码越顺眼，一条像样的意见都提不出来。"
- "🔥 在办公室改了一下午的项目，回家 git clone 下来想接着干。结果 Claude Code 跟头一回见这项目似的——全得我从头再讲一遍。讲到我自己都烦。"
- "🔥 Copilot 越更新我越想卸载——Cmd+I 那个框现在要加载半天，还跳出一堆我根本不需要的按钮。我受不了了，自己写了个插件。"

### 微信公众号
- "写完一个功能，按下回车，Claude 顺手帮我 review 了一遍，三条建议，全是夸我的。我盯着那三条看了半天，心里只有一个念头：它在审自己刚写的代码，我让贼来抓贼。"
- "那天在办公室改到一半的项目，我回家想接着弄。git clone 下来，打开 Claude Code，准备接着上午的活干。它问我：这个项目用的是哪个包管理器？"
- "有一天我按下 Cmd+I，等了三秒，出来的不是 diff，是一个"正在思考..."的 spinner，背后带着一个全屏的侧边栏面板。可是我只是想把一个函数名改短一点。"

### 知乎
- "先说一个反直觉的结论：让几个 AI 审同一份代码，最有价值的不是它们都点头的地方，而是它们打架的地方——分歧处，往往就是真 bug 藏身的地方。"
- "先说结论：如果你已经在用 Claude Code 或 Codex CLI，[quick-inline-suggestion] 值得装。它不是 Copilot 替代品，也不跟 Cursor 竞争。它只做一件事——把你已有的 CLI 工具接进 Cmd+I。完。"
- "结论放前面：Takeover v2 解决了一个具体的问题——Workflow agent 不能跑 Bash，而 v1 的整个模型派发链路就建在 Bash heredoc 上。"

### Twitter/X
- "A model reviewing its own code isn't a review. It can't catch what it couldn't catch the first time — same blind spots, same misses. The fix isn't a smarter model. It's a rival one."
- "Claude Code now writes its own memory. The catch: it lives in ~/.claude/ on your machine — not in the repo. Change something at the office. Clone it at home. Claude remembers none of it. Teammates? Same."
- "Every Claude Code user eventually hits the wall: Claude nails tool use but flubs hard math. DeepSeek reasons better but has no agent loop. So I stopped choosing. I built takeover."

---

## Closings I Use

### 小红书
- "👇 插件 ID：quick-inline-suggestion，扩展市场直接搜，或者去 GitHub 找 DawnEver/quick-inline-suggestion～"
- "👇 GitHub 搜 DawnEver/cc-market，takeover 就在里面，把连接交给你的 claude code 就行。想要直链评论区戳我～"
- "我想进化的不是代码，是人跟 AI 搭伙的方式：别再逼自己追上它的速度，让它学会替我省注意力。"

### 微信公众号
- "代码在 GitHub，没有加密，没有遥测，没有 telemetry 上报。你改什么代码、用什么提示词，只在你和你的 CLI 工具之间。"
- "代码在 GitHub，三百行，零依赖，连 heredoc 那行的来历都写在 commit 里，你可以自己翻。"
- "代码在 GitHub，`shared/attention.mjs` 拢共一百多行，零依赖，纯函数，每个字段、每条判据你都能自己翻、自己测。"

### 知乎
- "回过头看，sharp-review 想做的其实只有一件事：别让同一个脑子审自己的代码，让几家不同厂商的模型各看各的，把它们的分歧当成信号而不是噪声。"
- "回过头看这四个决策……有一个共同的逻辑：v1 证明了这件事有价值，v2 把每个卡点修到架构层面，而不是在表面贴胶带。"
- "在这个并行 AI 时代，有个数字是任何 benchmark 都测不出来的——我这一天，到底被打扰了几次。"

### Twitter/X
- "DeepSeek runs ~50x cheaper than Opus — a third independent opinion for the price of a rounding error."
- "Star it if you're tired of bloated AI editors. PRs welcome. 如果你也觉得 VS Code AI 越来越重，试试这个。⭐"
- "The scarce resource was never how fast AI works. It's the one thing that doesn't parallelize — me. Stop optimizing throughput. Budget the human."

---

## Voice Markers

- "就这样。没有……没有……没有……" — 用排比否定句列举自己去掉的东西，强调克制
- "先说结论……完。" — 知乎开头直接给判断，结尾一字收束
- "复制粘贴税" / "记忆跟着仓库走" / "内容和状态，分家" — 自创概念词命名痛点或架构主张，压成一句可复述的锚点
- "我让贼来抓贼" / "商业互吹" — 用俗语和自造词点破"模型自审"的盲区与空洞，一句立住核心论点
- "正则不会把codex看成claude。它没有'创造性'" — 反直觉洞察，用具体 bug 故事引出哲学总结
- "自动化焦虑" — 自创概念词命名 AI 时代的注意力危机，把抽象感受压成可复述的锚点
- "这道闸只管要不要打扰你，不管那件事还修不修" — 用生活化对比讲清技术边界，把架构决策翻译成直觉可感的承诺
- "加入光荣的进化吧" — slogan 双关收尾，从代码进化升维到人机协作方式进化
