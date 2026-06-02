# Step 08 — User Draft Review: MANDATORY READ-THROUGH

**Do NOT invoke review yet. Do NOT skip this step.**

三方会审 costs 18+ agent calls across all platforms. The user must read and approve every draft before review begins.

After all writer agents complete, present the generated articles:

```
📄 初稿已生成，请阅读

**生成结果**：
- 小红书：ongoing/<slug>/2-draft/xiaohongshu.md (<char_count> chars)
- 微信公众号：ongoing/<slug>/2-draft/wechat.md (<char_count> chars)
- 知乎：ongoing/<slug>/2-draft/zhihu.md (<char_count> chars)
- Twitter/X：ongoing/<slug>/2-draft/twitter.md (<tweet_count> tweets)

**请逐篇阅读，提出你的看法：**
- 角度和语气是否符合预期？
- 有没有需要调整的段落？
- 技术事实准确吗？
- 标题是否合适？（Gate 阶段选的标题可在此调整）

确认初稿后，进入**强制三方会审**。
```

Wait for the user to read and respond. This is mandatory.

- **If user requests changes** → edit article files directly, re-present affected articles, wait again.
- **If user wants to regenerate a platform entirely** → re-spawn that writer agent with the feedback, then re-present.
- **If user approves** ("可以审了" / "进入会审" / "review it") → proceed to Step 09 (三方会审).

> 🛑 This gate is mandatory. Never run 三方会审 before the user has read and okayed the drafts.
