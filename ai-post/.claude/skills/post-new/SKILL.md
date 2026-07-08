---
name: post-new
description: Generate platform-adapted articles from a GitHub repo, a local codebase, or a research report — spawns platform-specific agents for generation.
argument-hint: <github-url|local-path|slug> [platform]
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

# /post-new — Generate Articles from a Source

You are the orchestrator. Given a **source** — a GitHub repo URL, a local codebase directory, or a
local research report — resolve it, deeply ingest it (explore the code, or mine the report), research
the market landscape, write a structured analysis, then spawn platform-specific agents to generate
articles. See ## Source Kinds for how each source type is resolved.

## Pipeline

| Step | File | Gate |
|------|------|------|
| 01 | `01-clone.md` — Resolve source (github / local-dir / local-file), fetch metadata → `1-research/source.md` | — |
| 02 | `02-explore.md` — Ingest source: explore code OR mine report → `1-research/source-exploration.md` | — |
| 03 | `03-market-research.md` — WebSearch market landscape → `1-research/market-research.md` | — |

> Step 03 depends on Step 02: `03-market-research.md` reads `1-research/source-exploration.md` and extracts keywords/topics from it. Run 02 first, then 03 (03 may start from Step-01 metadata but is enriched by 02's output) — they are NOT dependency-free parallel.

| 04 | `04-analysis.md` — Consolidated analysis + article angles | — |
| 05 | `05-brief-gate.md` — ⭐ 选题确认 (angles + titles, iterate) | **User** |
| 06 | `06-spawn.md` — Spawn platform writers in parallel → `2-draft/v1/` | — |
| 07 | `07-images.md` — Plan image manifest from v1 drafts | — |
| 08 | `08-user-review.md` — ⭐ User reviews + edits → `v<N+1>/` (deltas only) | **User** |
| 09 | `09-review.md` — 🔒 三方会审 MANDATORY → fixes → next version | — |
| 10 | `10-summary.md` — Final confirm → assemble → images → publish | **User** |

## How to Execute

The argument is either a **source** (a new article — GitHub URL, local codebase path, or research-report
file path) or an existing `<slug>` (e.g. `owner--repo` or `owner--repo__topic`). **Before Step 01's
source detection, check whether the argument matches an existing `<slug>`** under `ongoing/` or
`archived/` — if so, route to resume per the Resume Table below rather than resolving it as a new source.

Run each step in order. **At the start of each step, Read the corresponding sub-file** and follow its instructions. The sub-file is the detailed playbook — this SKILL.md is just the map.

## Source Kinds

Step 01 resolves the argument to one of three kinds and records it in `ongoing/<slug>/1-research/source.md`
(the pointer every later step reads). The pipeline is source-agnostic downstream — Step 02 ingests into
`source-exploration.md` regardless.

| Kind | Argument looks like | How it's resolved | Under `repos/`? |
|------|--------------------|-------------------|-----------------|
| `github` | `owner/repo`, `https://github.com/owner/repo[.git]` | `git clone --depth 50` into `repos/<repo-slug>/` | clone dir |
| `local-dir` | a path to an existing directory | referenced **in place**, never copied | optional one-line pointer `repos/<repo-slug>.src` |
| `local-file` | a path to an existing file (`.pdf`/`.md`/`.txt`/…) | the research report is read **in place** as the primary material | nothing |

A **pointer file** — a `.src`/`.txt` whose content is a single filesystem path — is dereferenced to the
path it names, then re-classified as local-dir/local-file. This is the "text file that points to a
relative or absolute path" mechanism: a local source need not live under `repos/`. The external path is
never copied or (on cleanup) deleted — only the clone/pointer inside `repos/` is managed.

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
| `ongoing/<slug>/1-research/source-analysis.md` (no brief.md) | 05 Phase 1 |
| `ongoing/<slug>/1-research/market-research.md` | 04 |
| `ongoing/<slug>/1-research/source-exploration.md` | 03 |
| `ongoing/<slug>/1-research/source.md` (source resolved, not yet ingested) | 02 |
| `repos/<repo-slug>/` or `repos/<repo-slug>.src` exists (source cache; shared across articles) | 02 |
| nothing | 01 |

> Resume matches on `<slug>` (article-slug, possibly `<repo-slug>__<topic>`). The source-cache row is the only one keyed on `<repo-slug>` — a cached clone or local-dir pointer can serve a brand-new article.
> **Legacy fallback**: an in-flight article from an older run may still use `repo-exploration.md` / `repo-analysis.md` — if the `source-*` name is absent but the `repo-*` one exists, read it and continue (rename on next write).

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

Two distinct keys — the source cache is shared across articles, the working dir is per-article:

- **`<repo-slug>`** (source-slug) keys the source cache under `repos/`. For github → `owner--repo` (lowercased, `/` → `--`), a clone dir. For local-dir → the sanitized basename of the path, an optional `.src` pointer. For local-file → the sanitized report basename (nothing cached under `repos/`). One cached source serves every article written from it.
- **`<slug>`** (article-slug) keys the working dir under `ongoing/` and `archived/`. Defaults to `<repo-slug>` for the first/only article from a source. For **additional articles from the same source**, append a short topic suffix: `<repo-slug>__<topic>` (e.g. `dawneever--cc-market__sharp-review`). Lowercase, hyphenate the topic.

When to add a suffix: if `ongoing/<repo-slug>/` or any `archived/*/<repo-slug>/` already exists for a *different* topic, the new request is a **separate article** — derive `<slug> = <repo-slug>__<topic>` (topic from the user's angle) so it never clobbers the existing one. Confirm the chosen slug with the user at the step 05 brief gate.

If the user passes an existing `<slug>` (with or without suffix) directly, use the resume table above.
