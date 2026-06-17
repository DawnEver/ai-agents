---
name: post-new
description: Generate platform-adapted articles from a GitHub repo URL — spawns platform-specific agents for generation.
argument-hint: <github-url|slug> [platform]
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
  - Agent
  - Skill
  - WebFetch
  - WebSearch
---

# /post-new — Generate Articles from GitHub Repo

You are the orchestrator. Given a GitHub repo URL, clone and deeply explore the codebase, research the market landscape, write a structured analysis, then spawn platform-specific agents to generate articles.

## Pipeline

| Step | File | Gate |
|------|------|------|
| 01 | `01-clone.md` — Parse URL, clone repo, fetch gh metadata | — |
| 02 | `02-explore.md` — Deep code exploration → `1-research/repo-exploration.md` | — |
| 03 | `03-market-research.md` — WebSearch market landscape → `1-research/market-research.md` | — |

> Step 03 depends on Step 02: `03-market-research.md` reads `1-research/repo-exploration.md` and extracts language/topics from it. Run 02 first, then 03 (03 may start from Step-01 metadata but is enriched by 02's output) — they are NOT dependency-free parallel.

| 04 | `04-analysis.md` — Consolidated analysis + article angles | — |
| 05 | `05-brief-gate.md` — ⭐ 选题确认 (angles + titles, iterate) | **User** |
| 06 | `06-spawn.md` — Spawn platform writers in parallel → `2-draft/v1/` | — |
| 07 | `07-images.md` — Plan image manifest from v1 drafts | — |
| 08 | `08-user-review.md` — ⭐ User reviews + edits → `v<N+1>/` (deltas only) | **User** |
| 09 | `09-review.md` — 🔒 三方会审 MANDATORY → fixes → next version | — |
| 10 | `10-summary.md` — Final confirm → assemble → images → publish | **User** |

## How to Execute

The argument is either a GitHub URL (new article) or an existing `<slug>` (e.g. `owner--repo` or `owner--repo__topic`). **Before Step 01's URL parsing, check whether the argument matches an existing `<slug>`** under `ongoing/` or `archived/` — if so, route to resume per the Resume Table below rather than treating it as a URL.

Run each step in order. **At the start of each step, Read the corresponding sub-file** and follow its instructions. The sub-file is the detailed playbook — this SKILL.md is just the map.

## Resume Table (which step to enter on re-invocation)

Re-invoking `/post-new <slug>` resumes from the latest non-empty artifact:

| Existing artifact | Enter step |
|-------------------|-----------|
| `archived/*/<slug>/` (glob match — list all YYMMDD matches, let user pick) | Already archived — confirm: re-activate (move back to ongoing) or start fresh |
| `ongoing/<slug>/2-draft/v<N>/` + `brief.md` `finalized: true` | 10 (final — offer publish or regenerate) |
| `ongoing/<slug>/2-draft/v<N>/` (N >= 2) + `brief.md` `review_completed: true` | 08 (post-review — light edits or confirm final) |
| `ongoing/<slug>/2-draft/v1/` + `images.md` exists | 08 (drafts + image plan exist — user review) |
| `ongoing/<slug>/2-draft/v1/` but no `images.md` | 07 (drafts exist, need image plan) |
| `ongoing/<slug>/2-draft/` directory exists (empty) | 06 (re-spawn) |
| `ongoing/<slug>/1-research/brief.md` (has `titles_confirmed: true`) | 06 (spawn) |
| `ongoing/<slug>/1-research/brief.md` (has `angles_confirmed: true`, no titles yet) | 05 Phase 2 |
| `ongoing/<slug>/1-research/repo-analysis.md` (no brief.md) | 05 Phase 1 |
| `ongoing/<slug>/1-research/market-research.md` | 04 |
| `ongoing/<slug>/1-research/repo-exploration.md` | 03 |
| `repos/<repo-slug>/` exists (clone cache; shared across articles) | 02 |
| nothing | 01 |

> Resume matches on `<slug>` (article-slug, possibly `<repo-slug>__<topic>`). The clone-cache row is the only one keyed on `<repo-slug>` — a cached clone can serve a brand-new article.

`--restart-from <N>` jumps to any step. `--reclone` forces step 01 re-run.

## Hard Rules

- **Market research before analysis**: step 03 → 04.
- **Never skip user gates** (steps 05, 08, 10) — iterate until explicit approval.
- **Determine persona before writing** (step 05 Phase 0): set `persona: author|deep-user` in `brief.md` from `style/private/author-identity.md`; ask the user when uncertain. Writers bind narrator identity to it, not just tone.
- **三方会审 (step 09) is mandatory** — no path to publish without review.
- **Archive is frozen** — `archived/YYMMDD/<slug>/` never modified except `postmortem.md`.
- **Fanout is parallel** — step 06 spawns all writers in one message.
- **Platform metadata**: see `templates/_platform-registry.md` for the single source of truth.

## Slug

Two distinct keys — the clone cache is shared across articles, the working dir is per-article:

- **`<repo-slug>`** = `owner--repo` (lowercased, `/` → `--`). Keys the clone cache `repos/<repo-slug>/`. One clone serves every article written from that repo.
- **`<slug>`** (article-slug) keys the working dir under `ongoing/` and `archived/`. Defaults to `<repo-slug>` for the first/only article from a repo. For **additional articles from the same repo**, append a short topic suffix: `<repo-slug>__<topic>` (e.g. `dawneever--cc-market__sharp-review`). Lowercase, hyphenate the topic.

When to add a suffix: if `ongoing/<repo-slug>/` or any `archived/*/<repo-slug>/` already exists for a *different* topic, the new request is a **separate article** — derive `<slug> = <repo-slug>__<topic>` (topic from the user's angle) so it never clobbers the existing one. Confirm the chosen slug with the user at the step 05 brief gate.

If the user passes an existing `<slug>` (with or without suffix) directly, use the resume table above.
