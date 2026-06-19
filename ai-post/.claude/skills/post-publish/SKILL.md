---
name: post-publish
description: Export a finalized article for publishing — image verification, clipboard export, platform-specific publishing guidance. Does NOT edit content.
argument-hint: <platform> [project-slug]
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
---

# /post-publish — Platform Publishing

You handle the mechanics of getting content onto the platform. The article text is final — you do NOT edit, polish, or suggest content changes. All quality assurance (三方会审, user review) has already happened upstream.

## Supported Platforms

- `xiaohongshu` — 小红书
- `wechat` — 微信公众号
- `zhihu` — 知乎
- `twitter` — Twitter/X

> Per-platform metadata (publish URL, clipboard format, cover specs, checklist) lives in `_platforms/<platform>.md` — those are reference data, not workflow steps.

## Phase Table

| Phase | File | Steps |
|-------|------|-------|
| Identify | `01-identify.md` — Identify the article (walk-back inheritance) + BLOCKING review-verdict gate + image verification gate | 1–2 |
| Prepare | `02-prepare.md` — Platform-specific prep + Word export (wechat/zhihu) + clipboard + open browser | 3–4 |
| Publish | `03-publish.md` — Platform checklist + next steps | 5 |

## How to Execute

Run steps in order. **At the start of each phase, Read the corresponding sub-file** and follow its instructions. This SKILL.md is just the map.
