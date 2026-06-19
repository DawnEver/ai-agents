---
name: post-archive
description: Archive a finalized article and accumulate personal style fingerprints — moves to archived/YYMMDD/, updates style/profile.md
argument-hint: <slug>
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
---

# /post-archive — Archive & Style Accumulation

Archive a completed article slug. Distills `ongoing/<slug>/` into a frozen archive at `archived/YYMMDD/<slug>/` — research notes, the assembled final article per platform, the images those finals reference, and the latest review verdict. The raw `2-draft/vN/` version chain is collapsed (the final assembled output is kept, intermediate revisions are dropped). Then extracts style fingerprints and updates `style/profile.md`. No editing — the article text is final.

> **Archive contract** (what survives — Step 3 and the actual archived contents must match this exactly):
> - `1-research/` — copied verbatim
> - `<platform>.md` (one per platform) — the assembled final, version chain collapsed
> - `images.md` — the assembled final
> - `images/` — only the `-v<N>` files referenced by the final articles
> - `review-verdict.md` — the latest `2-draft/vN/review-verdict.md` (audit record of the passing 三方会审)
> - exported `.docx` (if produced by /post-publish) — kept alongside the platform finals
> - NOT preserved: the raw `2-draft/vN/` chain, draft-only scratch files

## Phase Table

| Phase | File | Steps |
|-------|------|-------|
| Identify | `01-identify.md` — Identify slug + BLOCKING review-verdict gate + verify final | 1–2 |
| Archive | `02-archive.md` — Assemble final & move to curated archive (copy only, no delete) | 3 |
| Style | `03-style.md` — Text-only style/published archive + fingerprint extraction + profile update | 4–6 |
| Cleanup | `04-cleanup.md` — Clone-cache cleanup + drop ongoing + optional postmortem + report | 7–9 |

## How to Execute

Run steps in order. **At the start of each phase, Read the corresponding sub-file** and follow its instructions. This SKILL.md is just the map.

> **Ordering (critical):** Step 3 only COPIES out of the version chain — it must NOT delete `ongoing/<slug>`. Steps 4–6 still read `2-draft/vN/`. The destructive `rm -rf "ongoing/<slug>"` cleanup is deferred to Step 7, AFTER every read from the version chain has completed.

## Hard Rule

Never modify files under `archived/YYMMDD/<slug>/` except for `postmortem.md`. The frozen snapshot is the source of truth.
