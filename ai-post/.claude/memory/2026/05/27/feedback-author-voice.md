---
name: feedback-author-voice
description: "Articles must be written in the repo author's voice, never third-party reviewer; banned AI-tell phrases"
metadata:
  type: feedback
created: 2026-05-27
accessed: 2026-05-27
tier: short
---

# Write as Repo Author, Not Reviewer

**Rule**: All generated articles must adopt the voice of the GitHub repo's author/maintainer. Write as "I built this" — first-person, firsthand knowledge. Never write as a third-party reviewer "discovering" a project.

**Banned AI-tell phrases** (these scream "AI wrote this"):
- 这篇文章 / 本文将 / 本文
- 总结一下 / 总的来说 / 综上所述
- 值得注意的是 / 值得一提的是
- 通过以上分析 / 通过对比可以发现
- Check out this article / In this thread I'll / Here's a breakdown

**Why**: The user noticed generated articles used "这篇文章" and other third-party reviewer phrasing that reads as obviously AI-generated. Content performs better when it feels like a developer sharing their own project, not a journalist reviewing someone else's.

**How to apply**: Templates are the single source of truth. All 4 templates updated with author-voice rules and banned-phrase lists. Agents load templates so they inherit automatically.

## GitHub Identity

**https://github.com/DawnEver is the user's personal GitHub account.** Any repo under this account is authored by the user — write as the creator, not a reviewer. This applies at the brief-gate stage too: adjust angles and titles to reflect first-person ownership before presenting them.
