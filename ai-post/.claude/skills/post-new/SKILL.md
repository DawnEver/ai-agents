---
name: post-new
description: Generate platform-adapted articles from a GitHub repo URL — spawns platform-specific agents for generation.
argument-hint: <github-url> [platform]
allowed-tools: "Read,Write,Bash,Glob,Grep,Agent,Skill,WebFetch,WebSearch"
---

# /post-new — Generate Articles from GitHub Repo

You are the orchestrator. Given a GitHub repo URL, clone and deeply explore the codebase, research the market landscape, write a structured analysis, then spawn platform-specific agents to generate articles.

## Pipeline

| Step | File | What Happens | Gate |
|------|------|-------------|------|
| 01 | `01-clone.md` | Parse URL, clone repo, fetch gh metadata | — |
| 02 | `02-explore.md` | Deep code exploration → `1-research/repo-exploration.md` | — |
| 03 | `03-market-research.md` | WebSearch: similar repos, trending, content gap → `1-research/market-research.md` | — |
| 04 | `04-analysis.md` | Consolidated analysis (folds in market research) + article angles → `1-research/repo-analysis.md` | — |
| 05 | `05-brief-gate.md` | ⭐ 选题确认 — angles + titles, iterate until approved | **User** |
| 06 | `06-images.md` | Image manifest + user-confirmed generation via `takeover-image` (covers → content, parallel) | **User** |
| 07 | `07-spawn.md` | Spawn platform writer agents in parallel → `2-draft/<platform>.md` | — |
| 08 | `08-user-review.md` | ⭐ Mandatory user read-through before review | **User** |
| 09 | `09-review.md` | 🔒 三方会审 — MANDATORY, cannot skip. Also reviews `2-draft/images.md` → produces `3-final/images.md` | — |
| 10 | `10-summary.md` | Present results, copy passed drafts to `3-final/` | — |
| 11 | post-archive | Move to `archived/YYMMDD/`, update style, optional postmortem | — |

## How to Execute

Run each step in order. **At the start of each step, Read the corresponding sub-file** and follow its instructions. The sub-file is the detailed playbook — this SKILL.md is just the map.

## Resume Table (which step to enter on re-invocation)

Re-invoking `/post-new <slug>` resumes from the latest non-empty artifact:

| Existing artifact | Enter step |
|-------------------|-----------|
| `archived/*/<slug>/` (glob match — list all YYMMDD matches, let user pick) | Already archived — confirm: re-activate (move back to ongoing) or start fresh |
| `ongoing/<slug>/3-final/<any-platform>.md` | 10 (reached final — offer publish or regenerate) |
| `ongoing/<slug>/2-draft/<any-platform>.md` | 08 (drafts exist — user review) |
| `ongoing/<slug>/2-draft/` directory exists (empty) | 07 (re-spawn — offer retry/skip/continue) |
| `ongoing/<slug>/2-draft/images.md` | 07 |
| `ongoing/<slug>/1-research/brief.md` (has `titles_confirmed: true`) | 06 |
| `ongoing/<slug>/1-research/brief.md` (has `angles_confirmed: true`, no titles yet) | 05 Phase 2 |
| `ongoing/<slug>/1-research/repo-analysis.md` (no brief.md) | 05 Phase 1 |
| `ongoing/<slug>/1-research/market-research.md` | 04 |
| `ongoing/<slug>/1-research/repo-exploration.md` | 03 |
| `repos/<slug>/` exists | 02 |
| nothing | 01 |

`--restart-from <N>` jumps to any step. `--reclone` forces step 01 re-run.

## Hard Rules

- **Market research before analysis**: step 03 → 04. Analysis folds in competitive landscape and content gaps.
- **Research and brief ALWAYS come before writing**: Never skip user confirmation gates.
- **User gates (steps 05, 08) are iterative**: Go back and forth until user explicitly approves.
- **三方会审 (step 09) is mandatory**: No article reaches publish without passing review.
- **Archive is frozen snapshot**: `archived/YYMMDD/<slug>/` is never modified after step 11 except for `postmortem.md`.
- **All intermediate files persist**: `ongoing/` during work, `archived/` after completion. Never delete working files except `repos/` (cached clone).
- **Fanout is parallel**: Step 07 spawns all writers in one message.

## Slug

Derive `<slug>` from the GitHub URL: `owner/repo` → `owner--repo` (lowercased, `/` → `--`). If user passes an existing slug, use the resume table above.
