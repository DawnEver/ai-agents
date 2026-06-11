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
