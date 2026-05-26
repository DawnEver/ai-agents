---
name: post-regenerate
description: Regenerate a single platform's article from an existing repo analysis without re-cloning.
argument-hint: <project-slug> <platform>
allowed-tools: "Read,Write,Bash"
---

# /post:regenerate — Redo One Platform

Regenerate the article for a single platform from an existing repo analysis. No re-clone, no re-analysis — just re-generate from `articles/<slug>/repo-analysis.md`.

## Workflow

1. Validate that `articles/<slug>/repo-analysis.md` exists. If not: "No analysis found. Run `/post:new <url>` first."
2. Validate platform is one of: `xiaohongshu`, `wechat`, `zhihu`, `twitter`.
3. Read `articles/<slug>/repo-analysis.md`.
4. Read the existing article `articles/<slug>/<platform>.md` if it exists — note what angle was used and what felt generic or clichéd.
5. Read the platform template: `templates/<platform>.md`.
6. Read `style/profile.md` if it exists — use accumulated personal style to guide tone.
7. **Apply anti-AI techniques** (Chinese platforms): run 创意排水 — based on the previous draft's angle, find a fresher entry point. Then generate the article. After drafting, execute 三遍审校 per `templates/审校checklist.md`.
7. Regenerate the article → overwrite `articles/<slug>/<platform>.md`.
8. Overwrite `articles/<slug>/<platform>.md` with the regenerated article.
9. Report: character count, key platform stats, AI味 grade overall (🟢/🟡/🔴), what angle changed vs previous draft, suggest `/post:publish <platform> <slug>`.
