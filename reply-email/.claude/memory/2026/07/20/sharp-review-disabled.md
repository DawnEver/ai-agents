---
name: sharp-review-disabled
description: Auto sharp-review is disabled repo-wide via astronomical thresholds in .claude/sharp-review.json — manual /sharp-review still works
metadata:
  type: project
---

The user asked to stop automatic sharp-review in this repo. The sharp-review plugin (cc-market)
has no `enabled: false` flag; its Stop hook reads trigger thresholds from the committed,
shareable `.claude/sharp-review.json` (via `scripts/lib/config.mjs` → `loadReviewConfig`).
The supported opt-out is setting unreachable thresholds there:

- `thresholds.wave0` / `thresholds.wave1`: 1,000,000 lines / 10,000 files
- `docsThreshold`: 10,000
- `codebaseIntervalMin`: 52,560,000 (~100 years)

With these, no source (diff wave gate, docs, codebase survey) ever fires, so the Stop hook
always exits silently. Manual `/sharp-review` invocation is unaffected.

**Why:** reply-email sessions almost only touch gitignored local data (`ongoing/`, `archived/`),
so the auto review never found reviewable changes and was pure overhead.

**How to apply:** To re-enable, delete `.claude/sharp-review.json` or lower the thresholds.
The same pattern works in any repo using the cc-market sharp-review plugin.
