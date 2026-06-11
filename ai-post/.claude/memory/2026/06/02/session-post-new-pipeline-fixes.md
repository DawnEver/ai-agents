---
name: 2026-06-02-post-new-pipeline-fixes
description: Full pipeline run for dawneever--cc-market (takeover v1.0.0); skill hardening across brief-gate, transitions, images.md relocation, and image prompt review
metadata:
  type: project
---

## Pipeline run: dawneever--cc-market (takeover v1.0.0)

Complete run — clone → explore → market research → analysis → brief gate → images → 4-platform spawn → user review → 三方会审 → 3-final.
All four platforms passed 三方会审 and are in `3-final/`.

## Skill hardening

### Brief gate persistence
- Added `brief.md` with `angles_confirmed` / `titles_confirmed` state fields
- Updated SKILL.md resume table to check brief.md instead of repo-analysis.md titles section
- **Why:** User pointed out brief gate wasn't persisted; session interruption caused loss of confirmed angles

### Transition patterns (from 3-final diff)
- User manually edited 3-final drafts for transitions. Diffing 2-draft vs 3-final revealed 6 systematic gaps.
- Updated all 3 CN templates (wechat, xiaohongshu, zhihu) with new rules under Connectives & Transitions
- Saved dedicated memory: [[transition-patterns-from-final-drafts]]
- **Why:** Generated drafts systematically miss connective tissue between motivation paragraphs, scene chains, and section headers

### Images.md relocation
- Moved images.md from `1-research/` to `2-draft/` (creative output, not research)
- Updated 06-images.md output path, SKILL.md pipeline table, SKILL.md resume table
- **Why:** Images are part of the draft phase, not research

### Image prompt review (Phase 6)
- Added Phase 6 to post-review SKILL.md: review `2-draft/images.md` against 3-final articles
- Output: `3-final/images.md` with prompts aligned to final terminology
- First run found 4 issues: GPT残留 ×2, 术语不一致, 封面标题不匹配
- **Why:** Image alt texts and AI prompts were never reviewed; terminology drift from drafts went undetected

## User Feedback

- Must show brief gate (angles + titles) before proceeding — hook interruption doesn't excuse skipping
- Transition words critical: motivation paragraphs need bridging ("但这个工作流"), scenes need chaining ("又比如"), sections need callback openers ("所以我写了")
- "我" authorship consistency throughout — never "作者" or "笔者"
- Image alt text must match final article terminology

## How to apply

When running /post:new:
1. Brief gate: write brief.md immediately on user confirmation; resume from it if interrupted
2. After spawn: check transitions before presenting to user (动机段衔接, 场景链式, 段落首句回扣, 段落拆分, 身份一致性)
3. After 三方会审: run Phase 6 image prompt review against 3-final drafts

## Publishing phase
- Image path convention changed: `1-research/images/` → `images/` (user stores images at slug root)
- Updated 06-images, 07-spawn, SKILL.md, post-publish SKILL.md — all `1-research/images` references purged
- Fixed `export_article.py`: reads from `ongoing/<slug>/3-final/` instead of `articles/<slug>/`
- Generated Word exports (wechat + zhihu), clipboard exports for all 4 platforms
- **Status**: Publishing in progress. Xiaohongshu clipboard ready. User needs to open publish URLs manually.
