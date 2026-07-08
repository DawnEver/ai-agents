---
name: feedback-ai-taste-patterns
description: Platform-specific AI-taste anti-patterns — what formats and phrases to ban from generation templates
metadata:
  type: feedback
---

小红书 and 知乎 generation had heavy AI-taste, while 微信公众号 was acceptable.

**Why:** The templates' Example Structure sections were steering agents toward rigid formats — 小红书's `🛠️ 核心功能：` + emoji-bullet catalog, 知乎's formal section headers (`## 项目概览`, `## 总结`). Agents followed these structures too literally.

**How to apply:** When templates produce AI-taste output, fix the template's Example Structure and banned patterns first — templates are single source of truth. Specific changes made:

- 小红书: Banned `🛠️ 核心功能：` + emoji-bullet feature catalogs. Features now woven into natural paragraphs.
- 知乎: Banned formal section headers (`项目概览`, `问题背景`, `上手体验`, `适用场景与局限`, `总结`). Headers must sound conversational or be skipped.
- 知乎: Added "需要承认的是", "解决的是一个边界很清晰的问题" to banned phrases.
- 知乎: Replaced "需要承认的是" in voice rule examples with "有个地方被我踩到了..." (matches actual author voice from [[feedback-author-voice]]).

See also: [[feedback-author-voice]] for the "write as author/maintainer, not reviewer" rule.

## 2026-07-08 — sentence-level AI tells (cc-lab harness 知乎/微信)

User-flagged "典型 AI 句子" in generated harness drafts — three recurring sentence-level tells (now added to `_writing-craft.md` Anti-AI Check → AI sentence patterns + Replacement Table):

1. **电报体断句 (telegraphic clipping)** — dropping subject/verb/object or a whole character to "sound concise," ending up choppy:
   - "**API trace 最高，作数；**" → "API trace 可信度最高；"
   - "稳定地拿到这些**数**" (dropped 据) → "…这些数据"
2. **生硬比喻当过渡/强调 (forced-metaphor verbs/nouns)** — a metaphor that doesn't land:
   - "下一节就**撞上了**" → "下一节就会讲到"
   - "还有个**更硬的坎**" → "还有个不容易注意的坑，卡了我好久" (concrete + relatable beats vague intensifier)
3. **为显口语硬凑的花哨说法 (forced vividness/slang)**:
   - "先说一个必须**拎出来的水分**" → "另外有一个必须拎出来说的问题"

Lesson: these slip past the banned-phrase check because they're *structural* tells, not fixed phrases. Read aloud; if a clause sounds clipped, or a metaphor is doing a transition's job, or a colloquialism feels manufactured, rewrite plain. Human voice ≠ maximally vivid — it's *natural*.
