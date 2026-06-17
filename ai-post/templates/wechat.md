---
platform: wechat
language: zh
emoji_density: see `templates/_platform-registry.md` (emoji_density) — moderate
---

# 微信公众号 Article Generation Instructions

## Platform DNA

微信公众号 is long-form, deep-analysis content. Readers subscribe and expect thoroughness — they are willing to invest 5-15 minutes. Articles that perform well combine technical depth with storytelling. The bar for quality is high: shallow content gets scrolled past. Readers expect to learn something substantial.

## Structural Formula

1. **Title (generated separately)** — Curiosity-driven or result-promising. Pattern: "[主体] 的 [特性]，[惊人结论]" or "[问题]？这个开源项目给出了答案"
2. **Opening (2-3 paragraphs)** — Start with a relatable pain point, industry context, or a personal story. Build tension. Make the reader think "yes, I've faced this too."
3. **Project Introduction (1-2 paragraphs)** — Who built it, why, and what problem does it solve. Include project background: is it from a big company? A solo dev? What was the motivation?
4. **Core Features Deep Dive (main body, 3-5 sections)** — Walk through each major feature in detail. This is the meat. For each feature:
   - What it does
   - Why it matters
   - How it works (include code snippets where instructive)
   - A concrete example
5. **Installation & Setup (step-by-step)** — A "保姆级教程" (nanny-level tutorial). Copy-paste ready commands. Show expected output. Cover common pitfalls.
6. **Advanced Usage (optional)** — For readers who want more. Configuration options, performance tuning, integration with other tools.
7. **Closing** — Summarize the project's significance. What does its existence mean for the ecosystem? End with the GitHub link as "阅读原文" (Read More).

## Voice Rules

- **Authoritative but accessible**: You know your stuff, but you explain it for someone who doesn't.
- **Tutorial-narrative hybrid**: Alternate between "here's why this matters" and "here's how you do it."
- Use "我们" (we) to include the reader in the learning journey. Avoid "笔者" (this author) — too formal.
- Storytelling is welcome: "想象一下，你正在..." (Imagine you're...)
- Slightly polished Chinese — not academic, but not casual chat either.
- Can use rhetorical questions to guide the reader's thinking.
- **BANNED phrases**: "这篇文章", "本文将", "总的来说", "值得注意的是", "综上所述", "通过以上分析" — these are AI tells. Write like a developer sharing their project, not like an essay.

## Code Block Rules

- Code blocks are EXPECTED. This is a technical tutorial platform.
- Show real, runnable code — preferably from the project's own examples.
- Always explain what the code does BEFORE showing it, then walk through key lines AFTER.
- Format: use markdown code fences with language tag.
- If the install is one command, that's fine in-line. If it's a config file, show the relevant section.

## Emoji Rules

- **Density**: canonical level in `templates/_platform-registry.md` (emoji_density: moderate) — craft target ~3-8 per article total. Use as section dividers or for emphasis.
- **Position**: Section headers can have an emoji. Don't emoji-prefix every paragraph.
- **Set**: 📌 ✨ 🚀 💡 ⚡ 🔧 — more subdued, professional set.
- **Don't**: Emoji on bullet lists. Readers find it noisy in long-form content.

## Technical Depth

- **Deep**. This is the platform for thorough technical content.
- Show installation, configuration, code examples, and output.
- Mention architecture decisions and trade-offs when relevant.
- Include comparison with alternatives (briefly, not a full Zhihu-style comparison).
- If there are benchmarks, cite them. If there are limitations, mention them honestly.

## Content Constraints

- **Length**: 2000-5000 characters. Under 1500 feels thin. Over 5000 needs to earn it.
- **Paragraphs**: 3-5 sentences max. Break often. Dense walls of text lose readers.
- **Code**: At least 2-3 code blocks showing real usage.
- **Images**: Reference with `[配图：描述]` placeholders. WeChat articles need visuals.
- **CTA**: End with the GitHub link as "阅读原文" (if the platform supports it) or directly: "GitHub: <url>"

## Example Structure

```
[Title]

## 引言
[Pain point + context — 2-3 paragraphs, build the "why should I care"]

## 项目介绍
[What it is, who built it, why it exists — 1-2 paragraphs]

## 核心功能解析

### 1. [Feature Name]
[What it does + why it matters — 1 paragraph]
[Code example — show the feature in action]
[What's clever about this — 1 paragraph]

### 2. [Feature Name]
[same pattern]

### 3. [Feature Name]
[same pattern]

## 快速上手
[Step 1: install]
[Step 2: basic usage]
[Step 3: see results]

## 实战案例
[Real-world use case with code]

## 总结
[Significance + link to GitHub]
```

## 封面图 (Cover Image)

微信公众号文章必须有一张封面图，显示在订阅号列表、朋友圈分享和文章顶部。封面图独立于正文配图，单独生成。

- **Aspect ratio**: see `templates/_platform-registry.md` (2.35:1 for 微信公众号).
- **Purpose**: 订阅号列表吸引点击 + 朋友圈分享卡片 + 文章顶部头图。读者决定是否点开的关键视觉。
- **Design notes**:
  - 封面图需要留出标题文字的安全区域（上方或居中偏上位置，微信会在底部叠加标题文字）
  - 项目名称/logo 作为视觉焦点
  - 避免过于密集的信息 —— 在订阅号列表中是缩略图尺寸
- **Output**: 封面图放在文章最开头，使用 markdown 图片引用：`![封面](../../images/wechat-cover-vN.png)`（路径取自 `images.md`，终版用真实版本号）

## 正文配图 (Content Images)

Image paths and counts: see `templates/_platform-registry.md`.

- **Format**: 在文章正文中直接使用 markdown 图片引用：`![中文说明](../../images/<id>-vN.png)`（从 `2-draft/vN/<platform>.md` 的相对路径，路径取自 `images.md`）
- **Aspect ratio**: `--ar 16:9` (微信公众号横版)
- **Number**: 3-5 张正文配图（长文需要视觉断点）
- **Image types for 微信公众号**:
  1. 项目架构图
  2. 安装/配置终端截图（真实操作截图优先）
  3. 代码输出或结果 demo（真实截图优先）
  4. 功能流程示意图
  5. 性能 benchmark 图（如有）

Example:
```
![项目架构图——从左到右：CLI入口→核心引擎→输出层](../../images/architecture-vN.png)
```

## Writing Quality

Read `templates/_writing-craft.md` for ALL universal writing techniques:
- Strong opening patterns + banned openers
- Microhumor density (every 200 chars ≥1)
- Concept handles
- Sentence rhythm + paragraph splitting
- Connectives & transitions (动机段衔接, 场景链式衔接, 段落首句回扣)
- 「我」as subject identity consistency
- Dopamine density
- Anti-AI check (banned phrases master list, AI味 grading 🟢🟡🔴)
- Paragraph mini-thesis
- 3-pass review process

This template contains only 微信公众号-specific rules. Apply BOTH files when generating.

## Generation Checklist

- [ ] 2000-5000 characters
- [ ] At least 2-3 code blocks with real usage
- [ ] Step-by-step installation included
- [ ] Strong opening (none of the 3 banned formulas)
- [ ] At least 1 microhumor moment per 200 chars
- [ ] 1-2 concept handles used
- [ ] Sentence rhythm varies (no 3+ consecutive same-length sentences)
- [ ] Connectives present: paragraph transitions not naked subject-verb starts
- [ ] No 3+ consecutive sentences with same opening structure
- [ ] Each paragraph has a dopamine point
- [ ] Each feature explained with "what + why + how"
- [ ] 封面图 present: `![封面](../../images/wechat-cover-vN.png)` at top of article
- [ ] GitHub link at the end
- [ ] 正文配图 present (3-5 markdown image refs, paths from images.md)
- [ ] 「我」主语覆盖：每段至少一句以"我"作主语，无整段以"项目/它/工具"为主语的段落
- [ ] Writing quality check complete (see `_writing-craft.md`) — no 🔴 paragraphs
- [ ] Reads as tutorial, not marketing
