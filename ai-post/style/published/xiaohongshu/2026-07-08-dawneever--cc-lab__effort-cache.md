---
platform: xiaohongshu
slug: dawneever--cc-lab__effort-cache
published: 2026-07-08
title: Claude 切 effort 会清缓存吗？实测别怕
---

# Claude 切 effort 会清缓存吗？实测别怕

🔥 用 Claude Code 的姐妹应该都有过这个纠结：想把思考档位 /effort 调低省点钱，手却不敢动——万一一切，之前缓存那一大坨全白烧，下一句还得重算，那不是更亏？我卡在这上头好久。

🧐 全网翻了个遍，居然没人讲清楚到底会不会。行吧，没人说我自己试。

😳 结果真有点意外：切 /effort 根本不会把缓存清空。它更像是给每个档位各存了一份——high 一份、low 一份，一个小时内都还在，互不打架。

📉 最爽的是切回去那一下：之前那份缓存原样复活，新建的 token 从一万多直接掉到一千出头，等于压根没重算、直接命中。省下来的肉眼可见。

🧩 所以结论特别简单：effort 就是个藏起来的「缓存分区」，不是一按就炸的开关。一个小时内 high、low 来回切，几乎不花钱，放心切、别再纠结了！

🙏 也说句老实话：我就在现在这个版本（cc 2.1.204）实测了一轮，不敢打包票往后版本永远这样。但至少当下，随便切。

🔧 对了，我是怎么「看见」这些的——自己搭了个小工具盯着 Claude Code 跑，叫 cc-lab（GitHub 搜 DawnEver/ai-agents 找 cc-lab ）。它的底座是我另一个插件 fabric，小白一行 /plugin install fabric@cc-market 就能装，我另一篇专门讲怎么玩。想要入口评论区戳我～

#ClaudeCode #AI编程 #程序员 #省钱攻略 #开源工具
