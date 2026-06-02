---
name: pipeline-upgrade-ongoing-archive-market-research
description: ai-post pipeline upgraded with paper-review patterns — market research step, ongoing/archive dirs, resume table
metadata:
  type: project
---

# Pipeline Upgrade: Market Research + Persistent Workspaces

## What Changed

Upgraded the ai-post pipeline following paper-review's mature patterns:

1. **New step 03 — Market Research**: WebSearch for similar repos, trending discussions, existing content coverage, and content gap analysis BEFORE writing analysis. Outputs `market-research.md` that feeds the brief gate. "Market research before analysis" (like paper-review's "literature before consensus").

2. **Directory restructure**: `articles/<slug>/` → `ongoing/<slug>/` with numbered phases (`1-research/`, `2-draft/`, `3-final/`), then `archived/YYMMDD/<slug>/` on completion. All intermediate files persist on disk (gitignored).

3. **Resume table**: SKILL.md now has a bottom-up artifact detection table — re-invoking with a slug auto-detects the next step.

4. **Archive behavior**: Move to `archived/` instead of delete. Frozen snapshot, never modified except `postmortem.md`.

5. **Renumbering**: Steps 03-09 shifted to 04-10. ~19 files updated.

**Why**: The old pipeline treated articles/ as transient (gitignored, deleted on archive), had no web search to gauge market demand, and couldn't resume mid-pipeline. Paper-review solved all three with ongoing/archive separation, a WebSearch literature step, and a resume table.

**How to apply**: All new articles go through `ongoing/<slug>/`. After publish, `/post:archive <slug>` moves to `archived/YYMMDD/`. Resume by re-running `/post:new <slug>`. The pipeline flow is now: clone → explore → market research → analysis → brief gate → images → spawn → user review → review → summary → archive.
