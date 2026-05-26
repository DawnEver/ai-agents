---
platform: wechat
character_limit: 2000-5000
language: zh
emoji_density: moderate
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

- **Write as the project's author/maintainer**: You created this tool. Share it with pride and firsthand knowledge, not as an outside observer reviewing someone else's work.
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

- **Density**: 3-8 per article total. Use as section dividers or for emphasis.
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

- **Aspect ratio**: `--ar 16:9`（大封面，订阅号列表展示）/ 正文顶部实际裁切为 2.35:1
- **Purpose**: 订阅号列表吸引点击 + 朋友圈分享卡片 + 文章顶部头图。读者决定是否点开的关键视觉。
- **Design notes**:
  - 封面图需要留出标题文字的安全区域（上方或居中偏上位置，微信会在底部叠加标题文字）
  - 项目名称/logo 作为视觉焦点
  - 避免过于密集的信息 —— 在订阅号列表中是缩略图尺寸
- **Output**: 封面图放在文章最开头，使用 markdown 图片引用：`![封面](images/wechat-cover.png)`

## 正文配图 (Content Images)

**核心原则**：图片路径来自 `articles/<slug>/images.md`，不要自行发明路径。优先使用项目真实截图（操作截图、终端输出等），AI 生成图作为补充。

- **Format**: 在文章正文中直接使用 markdown 图片引用：`![中文说明](images/<filename>)`
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
![项目架构图——从左到右：CLI入口→核心引擎→输出层](images/architecture.png)
```

## Anti-AI Writing Techniques

These are the techniques that separate human-voice writing from AI-generated text. Apply them during generation and the 3-pass review.

### 强开头 (Strong Opening)
Choose ONE formula — never use "在当今时代/随着XX的发展/越来越多的人":
- **具体事件开头**: Specific time + specific number + real reaction. Instantly creates authenticity.
- **钩子开头**: Raise a question, don't answer it. Create suspense.
- **反常识开头**: Challenge common assumptions, force the reader to ask "why?"

Opening checklist: first 3 sentences have specific details? Create at least 1 question/curiosity? First sentence has content (not filler)?

### 微幽默 (Microhumor)
Every 200 characters, at least 1 moment that makes the reader's corner of the mouth twitch upward. Not jokes — subtle real details:
- Unexpected specifics: "刷新了27次后台" not "很紧张"
- Self-deprecating honesty: "至少在我仅有的3次尝试中是这样"
- Exaggerated-but-true: "手机震到从桌上掉下来" not "反应很大"
- Funniest word at sentence end (Dave Barry technique)

AVOID: forced jokes, emoji stacking, trying-too-hard humor.

### 概念把手 (Concept Handles)
Create or use 1-2 concise phrases that capture complex ideas (e.g., "AI味", "创意水龙头"). These become the reader's mental hook. Introduce with a brief explanation the first time, use freely after.

### 句子节奏 (Sentence Rhythm)
Short (5-10 chars) + Medium (15-25 chars) + Long (25-35 chars) alternating. Never 3+ consecutive sentences of similar length. Read aloud to test — writing should "sing."

### 多巴胺密度 (Dopamine Density)
Every paragraph needs at least 1 "interesting" moment: unexpected insight, vivid example, precise metaphor, real detail, or microhumor. 3 consecutive paragraphs with nothing interesting = danger zone, inject content.

### 三遍审校 (3-Pass Review)
**Pass 1 — Content**: Facts accurate? Logic clear? Each paragraph has a mini-thesis (testable by summarizing each in one sentence)?  
**Pass 2 — Style**: Delete all套话 (在当今时代/综上所述/值得注意的是/需要强调的是). Simplify书面词 (显著提升→具体数字, 充分利用→用好). Add personal voice (明确观点 instead of "可能会"). Mark AI density: 🟢Low/🟡Medium/🔴High — rewrite 🔴 paragraphs.  
**Pass 3 — Detail**: Mark sentence lengths, find monotone regions, break with short/long sentences. Check paragraph length (3-5 lines on mobile). Read the whole article aloud.

## Generation Checklist

- [ ] 2000-5000 characters
- [ ] At least 2-3 code blocks with real usage
- [ ] Step-by-step installation included
- [ ] Strong opening (none of the 3 banned formulas)
- [ ] At least 1 microhumor moment per 200 chars
- [ ] 1-2 concept handles used
- [ ] Sentence rhythm varies (no 3+ consecutive same-length sentences)
- [ ] Each paragraph has a dopamine point
- [ ] Each feature explained with "what + why + how"
- [ ] 封面图 present: `![封面](images/wechat-cover.png)` at top of article
- [ ] GitHub link at the end
- [ ] 正文配图 present (3-5 markdown image refs, paths from images.md)
- [ ] 3-pass review completed — no 🔴 AI-toned paragraphs remaining
- [ ] Reads as tutorial, not marketing
