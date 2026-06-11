---
name: sharp-review-2026-06-11
description: Sharp review findings — 2 total
metadata:
  type: project
---

## Review 2026-06-11 (session) — current branch

### Reviewer Status
- Reviewer A (Codex): skipped
- Reviewer B (DeepSeek): OK
- Reviewer C (Sonnet): OK

### Confirmed findings

---

### [SR-20260611-001] [HIGH] ai-post/.claude/rules/MEMORY.md — Memory index lost all descriptive summaries, now displays only timestamps — drastically reduces usability for humans scanning the index.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Restore meaningful summaries (ideally pulled from the description frontmatter of each memory file) or at least keep the manual descriptions that previously existed.

Previously, entries like '26 findings: pipeline bugs, memory system issues' provided immediate context. The diff replaces every meaningful summary with bare created: and accessed: fields. The index is now a list of dates, forcing users to open each file to understand its content. This is a significant UX regression and architectural oversight — an index should aid discoverability, not hide it.

---

### [SR-20260611-002] [MEDIUM] ai-post/.claude/rules/MEMORY.md — Link text for 'session-post-new-pipeline-fixes' contains a duplicate date prefix, causing inconsistency and confusion.

- **Category:** Bug
- **Status:** OPEN
- **Suggestion:** Remove the redundant '2026-06-02' from the link text; use the slug alone or a concise label.

The line reads '- [2026-06-02 2026-06-02-post-new-pipeline-fixes](...)'. The date is already encoded in the file path, and other entries do not repeat it, making this a likely copy-paste error.
