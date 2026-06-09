# Memory Index

<!--
Three-tier memory system:
  1. Rules (.claude/rules/)          — always injected; core behavioral constraints only
  2. Long-term memory (tier: long)   — progressive disclosure; demoted to short if inactive
  3. Short-term memory (tier: short) — progressive disclosure; 90d eviction

Frontmatter fields (memory files):
  created:  ISO date — set at creation, IMMUTABLE
  accessed: ISO date — bumped on reference
  tier:     long | short (default short)

Lifecycle scripts (run manually as needed):
  touch-memory.js <path> [--promote]  — bump accessed; --promote upgrades short → long
  prune-memory.js [--evict-stale]     — evict stale short-term; demote untouched long-term
  compact.js [--check]                — check index size; compact when large
-->

## Tasks

- [Active Tasks](../memory/tasks/tasks.md) — `created: 2026-06-04, accessed: 2026-06-09` — 0 open

## Recent

- [2026-06-09 sharp-review-2026-06-09](../memory/2026/06/09/sharp-review.md) — `created: 2026-06-09, accessed: 2026-06-09`
- [2026-06-09 thread-archive-prev-link](../memory/2026-06-09/thread-archive-prev-link.md) — `created: 2026-06-09, accessed: 2026-06-09`
- [2026-06-09 rem-1-0-9-broken](../memory/2026-06-09/rem-1.0.9-broken.md) — `created: 2026-06-09, accessed: 2026-06-09`
