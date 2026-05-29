---
name: paper-review
description: Review an academic paper PDF — ingest, summarise, fan out multi-angle 锐评, polish user draft into publishable English reviewer comments, archive.
argument-hint: <path-to.pdf-or-slug>
allowed-tools: "Read,Write,Bash,Glob,Grep,Agent,Skill,WebFetch,WebSearch"
---

# /paper-review:new — Review a paper

You are the orchestrator. Given a PDF path (or a slug already in `ongoing/`), walk the eight-step pipeline.

## Pipeline

| Step | File | What happens |
|------|------|--------------|
| 1 | `01-ingest.md` | marker-pdf → `1-paper-text/paper.md` + `md/` + `img/sec*` + `INDEX.md` |
| 2 | `02-consensus.md` | ⭐ Write `2-review/summary.md` — shared truth (+ `Obvious gaps`), user confirms |
| 2b | `02b-literature.md` | Search top N references (from paper + IEEE Xplore) → `2-review/literature.md` |
| 3 | `03-angle-gate.md` | ⭐ Propose angles, user confirms |
| 4 | `04-fanout.md` | Spawn reviewers in parallel (Sonnet + takeover) |
| 5 | `05-aggregate.md` | Merge into `2-review/critiques.md` |
| 6 | `06-user-draft.md` | ⭐ Orchestrator generates complete draft, user edits (hard gate, session boundary) |
| 7 | `07-polish.md` | `polisher-english` → `3-response/final.md` (plain text) |
| 8 | `08-archive.md` | Move to `archived/`, update global style + angles, optional postmortem |

## How to execute

At the start of each step, Read the corresponding sub-file and follow it. This file is the map — sub-files are the playbook.

## Resume table (which step to enter on re-invocation)

Re-invoking `/paper-review:new <slug>` resumes from the latest non-empty artifact:

| Existing artifact | Enter step |
|-------------------|-----------|
| `archived/<slug>/3-response/final.md` | 08 already done — confirm with user, use `/paper-review:rerun` instead |
| `ongoing/<slug>/3-response/final.md` | 08 |
| `ongoing/<slug>/3-response/draft.md` (non-empty) | 07 |
| `ongoing/<slug>/2-review/critiques.md` | 06 |
| `ongoing/<slug>/2-review/critiques/*.md` (all angles present) | 05 |
| `ongoing/<slug>/2-review/critiques/*.md` (partial — fewer files than angles in `angles.md`) | 04 (incomplete fanout — offer retry/skip/continue) |
| `ongoing/<slug>/2-review/angles.md` | 04 |
| `ongoing/<slug>/2-review/literature.md` (non-empty) | 03 |
| `ongoing/<slug>/2-review/summary.md` | 02b |
| `ongoing/<slug>/1-paper-text/paper.md` | 02 |
| nothing | 01 |

Pass `--restart-from <N>` to jump directly to a step, e.g.:
- `--restart-from 04` — re-run fanout without re-ingesting or re-summarising.
- `--restart-from 02` — rebuild the summary after fixing a bad ingest.

Pass `--reingest` to force re-running step 01 even if `1-paper-text/paper.md` already exists. Use when the ingest produced poor section splits, included noise, or missed appended papers. Without `--reingest`, an existing `paper.md` causes step 01 to be skipped and resume enters at step 02.

**Partial fanout**: if `2-review/critiques/` contains some but not all expected `<angle>.md` files (fewer files than angles in `angles.md`), the fanout did not complete. On resume, offer the user: retry missing reviewers, or continue with partial results. Do not silently enter step 05 with a partial set.

## Hard rules

- Every downstream agent **must read `summary.md` first**. No opinion without consensus.
- Steps 3 and 6 are **user gates** — iterate until the user approves; never skip.
- Step 6 is a **session boundary**: pipeline yields control back to the user. Resume by re-invoking with the slug after `draft.md` is written.
- Fanout (step 4) is **parallel** — one message, multiple Agent/Skill calls.
- Routing comes from each reviewer agent's frontmatter `router:` field. Step 03 may override per-paper into `angles.md`. Step 04 reads: override > frontmatter default.
- Polish (step 7) **never invents content** — every claim must trace to `draft.md`. Output is plain text, no markdown.
- Archive (step 8) **always** updates `style/profile.md` and `critiques-library/angles.md`, with dedup and rolling-window caps.

## Slug

Derive `<slug>` from the PDF filename (lowercase, non-alphanum → `-`, strip leading/trailing `-`). If the user passes an existing slug, use the resume table above.
