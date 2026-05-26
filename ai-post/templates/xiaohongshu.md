---
platform: xiaohongshu
character_limit: 800-1000
language: zh
emoji_density: high
---

# 小红书 Article Generation Instructions

## Platform DNA

小红书 is short-form, high visual density, emotion-driven content. Readers scroll fast through a feed and decide in 1-2 seconds whether to stop. Your article must hook instantly and deliver value in a skimmable format. The tone is "a friend sharing a cool discovery" — not a teacher, not a salesperson.

## Structural Formula

1. **Hook line (1 sentence)** — Lead with a strong emoji + pain point or surprising claim. Make the reader think "I need this."
2. **What is it (1 sentence)** — Name the tool/project and what it does, in plain language.
3. **Pain point expansion (1-2 sentences)** — Why the existing way sucks. Make the reader nod.
4. **Features as conversation (2-3 natural paragraphs, NOT a bullet catalog)** — Weave features into natural chat. Lead with what surprised you or what's actually useful. Describe the experience, not the feature name. One paragraph can cover 2 related features. The emoji-bullet catalog format (`🛠️ 核心功能：` + `✨ Feature 1` + `⚡ Feature 2`) is BANNED — it reads like a product spec sheet and screams AI.
5. **Highlights (1-2 standout details)** — One or two things only the builder would know. A bug you fought, a design decision, a clever trick. Told as a short story, not a bullet point.
6. **CTA (Call to Action)** — One casual line. Since 小红书 limits external links, guide to comments or homepage for the link.

## Voice Rules

- Use "我" (I) and "你" (you) — personal, direct, conversational
- **Write as the project's author/maintainer**, not a third-party reviewer. You built this. You're sharing your own work.
- Sound like a friend who just found something amazing, not a tech reviewer
- Short sentences. Break long ones.
- One-sentence paragraphs are fine. Walls of text are death.
- NO marketing speak. NO "revolutionary" / "game-changing" / "next-gen"
- **BANNED phrases** (these scream "AI wrote this"): "这篇文章", "本文将", "总结一下", "总的来说", "值得注意的是", "综上所述"
- **BANNED formats**: Structured emoji-bullet feature catalogs (`🛠️ 核心功能：` + `✨ Feature 1` + `⚡ Feature 2` ...) — this reads like a product spec sheet, not a 小红书 post. Weave features into natural conversation instead.
- If you wouldn't say it to a friend over coffee, don't write it

## Emoji Rules

- **Density**: 8-15 emojis per article (~1 per 60-80 characters)
- **Position**: Every bullet point starts with an emoji. Headline has one. CTA has one.
- **Preferred set**: 🔥 🚀 💡 ✨ 🛠️ 👨‍💻 📌 💻 🎯 ⚡ 🎉 🔗 ⭐ 💬 👇
- **Pattern**: Use emojis as visual bullet markers and emotional amplifiers
- **Don't**: Stack multiple emojis in a row. One is enough.

## Technical Depth

- **Shallow to moderate**. This is NOT a technical tutorial.
- No code blocks unless they are 1-3 lines and highly illustrative (e.g., a one-liner install command)
- Prefer describing visual results over showing code: "一键生成漂亮的文档页面" not a code snippet
- Mention tech stack only if it's a selling point (e.g., "基于 Rust 构建，速度极快")

## Content Constraints

- **Length**: ~800-1000 characters total
- **No external links in body** — 小红书 may hide posts with links. Use "评论区/主页自取" pattern.
- **Hashtags**: Suggest 3-5 relevant hashtags at the end (e.g., #开源工具 #程序员必备 #效率提升)
- **Image placeholders**: Include bracketed descriptions like `[配图：项目主页截图]` where visuals would go

## Example Structure

```
🔥 [Hook: pain point or surprising result — one sentence that makes the reader stop scrolling]

[What it is + what it does — 1-2 sentences, plain language, no hype]

![配图](images/xxx.png)

💡 [Why you built it / why it matters — 1-2 sentences. Personal motivation, not market analysis.]

✨ [Features woven into natural paragraphs, NOT a catalog. Each paragraph covers 1-2 features in a conversational way. Lead with what's surprising or useful, not a feature name.]

![配图](images/xxx.png)

⭐ [One or two standout details — the stuff you only learn from actually building it. Technical but told as a story.]

👇 [CTA — casual, one line. How to find it.]

#hashtag1 #hashtag2 #hashtag3
```

**Critical anti-pattern** — Do NOT write this:
```
🛠️ 核心功能：
✨ Edit 模式：告诉它改什么...
⚡ Ask 模式：输入框里打个问号...
🚀 双后端自动切换：...
📌 历史指令：...
```
This is a product spec sheet, not a 小红书 post. It screams AI. Instead, mention features in passing as part of a conversation: "用下来最爽的几个点..." then describe them naturally, no rigid emoji:label format.

## 封面图 (Cover Image) ⚠️ 单独设计

小红书封面图是决定笔记点击率的首要因素。用户在 feed 中快速滑动，封面图必须在 1 秒内传达价值和好奇心。封面图与正文配图的**设计逻辑完全不同**，必须单独设计。

### 封面图 vs 正文配图

| | 封面图 | 正文配图 |
|---|---|---|
| 目的 | 吸引点击、feed 中脱颖而出 | 辅助说明内容 |
| 是否有文字 | ✅ 必须有标题/钩子文字 | ❌ 纯视觉 |
| 设计感 | 高——需要排版、配色、对比度 | 中——截图/示意图即可 |
| 信息密度 | 低——一个核心信息足矣 | 中-高——解释性图表 |

### 封面图设计规范

- **Aspect ratio**: `--ar 3:4`（小红书竖屏封面）
- **Purpose**: Feed 流中吸引点击。读者看到封面的第一秒决定是否点进来。
- **必须包含的元素**:
  1. **钩子文字（中文）** —— 封面上的标题文字，通常 1-2 行，字体大且醒目。直接来自文章的钩子句或标题。
  2. **项目名称/logo** —— 小字或角标位置
  3. **视觉主体** —— 产品截图、代码效果图、或抽象科技图形
- **设计要点**:
  - 文字与背景高对比度（深色背景+白色文字 / 浅色背景+深色文字）
  - 文字区域占封面 30-50%，不要太小（feed 中是缩略图）
  - 避免白色背景（feed 中不突出），优先深色或高饱和背景
  - 风格：现代科技产品图 / 开发者工具深色主题 / 扁平插画
- **Output**: 封面图放在文章最开头，使用 markdown 图片引用 `![封面：钩子文字](images/xhs-cover.png)`。封面图不计入正文配图数量。

## 正文配图 (Content Images)

**核心原则**：图片路径来自 `articles/<slug>/images.md`，不要自行发明路径。优先使用项目真实截图（GIF、操作截图等），AI 生成图作为补充。

- **Format**: 在文章正文中直接使用 markdown 图片引用：`![中文说明](images/<filename>)`
- **Aspect ratio**: `--ar 3:4` (小红书竖屏图表现最好)
- **Number**: 2-3 张正文配图（小红书是视觉平台，图片必不可少）。封面不计入。
- **Image types for 小红书**:
  1. 项目主界面 / 操作截图（来自项目真实产出，如有）
  2. 使用前后对比，展示痛点被解决
  3. 核心功能特写或结果 demo

Example:
```
![项目主界面——深色IDE风格，代码高亮，左侧文件树右侧编辑器](images/product-shot.png)
```

## Anti-AI Writing Techniques

### 强开头 (Strong Opening — First Line is Life or Death)
- **痛点直击**: Describe the exact frustrating scenario the reader is living right now
- **惊人结论**: Lead with the result, make them want to know how
- BANNED: 随着XX发展 / 今天来分享一个 / 最近发现了 / 相信很多小伙伴

### 微幽默 (Microhumor)
At least 1 moment that makes the reader smile. Small, real, specific:
- Unexpected number: "我试了23次才搞定" not "试了很多次"
- Self-deprecating: a small real failure before the win
- Exaggerated-but-true description of the pain point

### 降AI味自查 (Anti-AI Check)
Before finalizing, read every sentence aloud:
- ❌ Delete: 这篇文章 / 本文将 / 总结一下 / 总的来说 / 值得注意的是 / 综上所述
- ❌ Delete: 显著提升 / 充分利用 / 进行操作 / 相关功能 / 有效提升
- ❌ Delete: anything you wouldn't say to a friend over coffee
- ✅ Keep: specific numbers, real reactions, casual expressions
- Grade each paragraph: 🟢 human / 🟡 slightly AI / 🔴 AI-bot (must rewrite 🔴)

## Generation Checklist

Before finalizing, verify ALL of these:
- [ ] 800-1000 characters (under 600 = too thin, over 1000 = cut)
- [ ] 8-15 emojis total, every bullet starts with one
- [ ] First line is a strong hook (pain point or surprising result)
- [ ] At least 1 microhumor moment
- [ ] CTA present (comment/homepage pattern)
- [ ] No markdown code fences (```)
- [ ] No external URLs in body
- [ ] 3-5 hashtags suggested
- [ ] 封面图 present: `![封面：...](images/xhs-cover.png)` at top of article
- [ ] 正文配图 present (2-3 markdown image refs, paths from images.md)
- [ ] Anti-AI check complete — no 🔴 paragraphs
- [ ] Sounds like a friend sharing, not a press release
