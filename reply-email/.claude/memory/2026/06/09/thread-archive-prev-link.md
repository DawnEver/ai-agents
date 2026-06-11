---
name: thread-archive-prev-link
description: Multi-turn email threads use per-round folders with prev: links — no more stacked original-N.txt files
metadata:
  type: project
---

Archive structure changed: each exchange round in a thread gets its own dated folder (`archived/YYYY-MM-DD/<topic>/`). The `meta.md` for continuation rounds includes a `prev:` relative path to the immediately preceding round's folder instead of stacking `original-2.txt`, `original-3.txt` in one directory.

**Why:** Avoids duplicating prior email content on every archive step; thread history is reconstructed by following `prev:` links.

**How to apply:** When archiving a thread continuation, create a new dated folder for the current round only. Set `prev: ../../YYYY-MM-DD/<topic>` in meta.md pointing to the previous round.
