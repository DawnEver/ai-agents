---
name: post-regenerate
description: Regenerate a single platform's article from an existing repo analysis without re-cloning.
argument-hint: <project-slug> <platform>
allowed-tools:
  - Read
  - Write
  - Glob
  - Agent
---

# /post-regenerate — Redo One Platform

Regenerate the article for a single platform from an existing repo analysis. No re-clone, no re-analysis — just re-generate from `ongoing/<slug>/1-research/repo-analysis.md`.

## Workflow

1. Validate that `ongoing/<slug>/1-research/repo-analysis.md` exists. If not: "No analysis found. Run `/post-new <url>` first."
2. Validate platform is one of: `xiaohongshu`, `wechat`, `zhihu`, `twitter`.
3. Read `ongoing/<slug>/1-research/repo-analysis.md`.
4. Read `ongoing/<slug>/1-research/market-research.md` — use market context for fresh angle.
5. Walk `ongoing/<slug>/2-draft/` to find the latest version containing `<platform>.md` — note what angle was used and what felt generic or clichéd.
6. Read the platform template: `templates/<platform>.md`.
7. Read `style/profile.md` if it exists — use accumulated personal style to guide tone.
8. **Apply anti-AI techniques** (Chinese platforms): run 创意排水 — based on the previous draft's angle, find a fresher entry point. Then generate the article. After drafting, execute 三遍审校 per `templates/审校checklist.md`.
9. Determine the next version number (scan `2-draft/vN/` directories, increment).
10. Create `2-draft/v<N+1>/` directory.
11. Regenerate the article → write to `2-draft/v<N+1>/<platform>.md`. Other platforms unchanged (inherit from prior version). If `brief.md` has `finalized: true`, reset it to `false` and clear `review_completed` — the old final is now stale. Warn: "New version created. Re-run review and step 10 final confirmation before publishing."
12. Report: character count, key platform stats, AI味 grade overall (🟢/🟡/🔴), what angle changed vs previous version, suggest re-running review.
