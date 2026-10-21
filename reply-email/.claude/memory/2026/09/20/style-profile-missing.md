---
name: style-profile-missing
description: "style/ is entirely absent from reply-email, so AGENTS.md step 7c (promote diff patterns to style/profile.md) cannot run — every draft falls back to inferring voice from recent archives"
metadata:
  type: project
---

`style/profile.md` — the authoritative voice source named in AGENTS.md (*Style*, and step 3 /
step 7c of the replying workflow) — does not exist, and neither does the `style/` directory
itself. The only `profile.md` anywhere under `ai-agents/` belongs to the unrelated `ai-post`
project.

**Consequences:**

- Step 3 of the replying workflow always takes the fallback branch: infer voice from the ~5 most
  recent archived replies. That works (the house voice is consistent and legible: plain
  `Hi <first name>,`, `Best,` + first name, blank line between every line, no closing-invitation
  lines) but it is re-derived from scratch every single round.
- Step 7c cannot run. Diff observations still land in each round's `meta.md`, so the raw material
  for promotion accumulates, but nothing is ever promoted. Every round's diff notes therefore
  read "single instance, no promotion" — which is exactly the systematic under-promotion that
  `2026-07-30/archive-audit-style-promotions.md` documented and fixed once already.

**Why it looks lost rather than never-created:** the 2026-07-30 memory records a full-archive
audit that rebuilt `style/profile.md` with a `## Last updated` log and six promoted rules
(inline phrasing over "I've attached", short sentences over em-dash run-ons, no echo-back of the
sender's own numbers, no self-deprecation, concrete over vague, and the closing-invitation
exception for outgoing-initiated mail). The file that audit produced is gone — most likely
dropped in the OneDrive migration, where `archived/` was relocated under
`Sync/agent-data/reply-email/` and `style/` was not carried over.

**How to apply:** treat this as a known gap, not a mystery. Until it is fixed, infer voice from
the five newest archived `reply.md` files each round and say so. The fix is to re-run the
`2026-07-30` audit procedure: read every `archived/**/meta.md`, group the `## Diff notes` entries
by theme, count distinct archives per theme, and promote any theme appearing in ≥2 archives into
a rebuilt `style/profile.md`. Note that `style/` is gitignored, so a rebuild is device-local —
whichever machine rebuilds it, the other will still see the gap unless the file is synced.
