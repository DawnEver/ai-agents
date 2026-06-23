---
name: thread-archive-prev-link
description: Multi-turn email threads use per-round dated folders with prev: links — no stacked original-N.txt files
metadata:
  type: project
---

Each exchange round in a thread gets its own dated folder under the nested layout
`archived/YYYY/MM/DD/<topic>/` (AGENT.md is authoritative). When the same slug archives more
than once on the same date, later rounds take a `-r<N>` suffix (`<topic>-r2`, `<topic>-r3` …).
The `meta.md` for continuation rounds carries `round: <N>` and a `prev:` relative path to the
immediately preceding round's folder, instead of stacking `original-2.txt`, `original-3.txt` in
one directory.

**Why:** Avoids duplicating prior email content on every archive step; thread history is
reconstructed by slug-based globbing (prev: is cosmetic).

**How to apply:** When archiving a thread continuation, create a new dated folder for the
current round only and set `prev: ../../../../YYYY/MM/DD/<topic>` in meta.md pointing to the
previous round.
