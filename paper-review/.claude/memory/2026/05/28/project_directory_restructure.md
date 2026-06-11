---
name: project-directory-restructure
description: Pipeline directory layout changed to 0-raw.pdf / 1-paper-text / 2-review / 3-response
metadata:
  type: project
---

Directory layout restructured from flat to numbered-phase (2026-05-28).

**Why:** The flat layout (all files in slug root) became cluttered. User requested `0-raw.pdf, 1-paper-text, 2-review, 3-response` to make pipeline stages explicit.

**New structure:**
```
ongoing/<slug>/
  0-raw.pdf               ← original PDF
  1-paper-text/            ← Step 01: ingested text, sections, images, INDEX.md, appended/
  2-review/                ← Steps 02-05: summary.md, angles.md, critiques/, critiques.md
  3-response/              ← Steps 06-07: draft.md, final.md
archived/<slug>/           ← mirrors ongoing/ 0-1-2-3 structure
```

**How to apply:** All path references updated across ~16 files (SKILL.md, 01-08 step files, 4 reviewer agents, polisher, AGENT.md, paper-rerun/SKILL.md, ingest.py). sed-based bulk replacement + manual edits for layout docs. Old ongoing/ papers need re-ingest or manual migration.
