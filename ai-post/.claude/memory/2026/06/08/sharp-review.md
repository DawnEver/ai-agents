---
name: sharp-review-2026-06-08
description: Post-feature sharp review — 15 findings across MEMORY.md broken links, dropped knowledge entries, cost claims, Agent() syntax, Codex CLI pre-check
metadata:
  type: project
created: 2026-06-08
accessed: 2026-06-08
tier: short
---

# Sharp Review 2026-06-08

15 findings from 3 parallel reviewers on image-workflow + memory-system diff. All fixed.

## Key fixes applied

### MEMORY.md (SR-001,002,004,006,007,013,015)
- Removed 11 dead SR links pointing to non-existent memory/2026-06-06/ files
- Restored 5 dropped knowledge entries that still existed on disk
- Split into `## Knowledge (long-term)` and `## Tasks (sync-tasks.js)` sections
- Removed conflicting management comments

### Pipeline docs (SR-003,011)
- AGENT.md command table: `review → archive` → `review → 3-final`
- README pipeline: `三方会审 → archive` → `三方会审 → publish → archive`

### Image workflow (SR-008,009,010)
- 06-images.md: upgraded from "optional" to mandatory Phase 2 with Codex CLI pre-check
- takeover-image.md + 06-images.md: added cost caveats (`~30K+`, "measure to calibrate")
- Agent() pseudo-syntax replaced with correct Agent({}) syntax

### Tasks (SR-005,012,014)
- tasks.md: timestamp updated, SR-002 resolved and archived
- archive/2026-06.md: added bulk resolution note, SR-002 entry

### Templates (pre-existing, fixed alongside)
- xiaohongshu/wechat/zhihu templates: `articles/<slug>/images.md` → `ongoing/<slug>/2-draft/images.md`
