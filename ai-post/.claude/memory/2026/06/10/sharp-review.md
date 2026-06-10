---
name: sharp-review-2026-06-10
description: Sharp review findings — 9 total
metadata:
  type: project
created: 2026-06-10
accessed: 2026-06-10
tier: short
---

## Review 2026-06-10 (session) — current branch

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): skipped
- Reviewer C (Sonnet): OK

### Confirmed findings

---

### [SR-20260610-001] [HIGH] .claude/skills/post-review/SKILL.md — BOM (U+FEFF) character prepended to YAML frontmatter — breaks YAML parsers

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Strip the BOM byte from the file; save as UTF-8 without BOM.

---

### [SR-20260610-002] [MEDIUM] .claude/skills/post-review/SKILL.md — Hardcoded absolute Windows path to sharp-review-workflow.js — not portable across machines or OSes

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** high-confidence (≥2 reviewers)
- **Suggestion:** Replace with a relative path or reference by plugin name.

---

### [SR-20260610-003] [MEDIUM] .claude/skills/post-new/08-user-review.md — images.md path mismatch

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Change presentation path to match actual location from step 07.

---

### [SR-20260610-004] [LOW] templates/wechat.md — Template image path is wrong relative to article location

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Change to ../../images/<filename> in all three templates.

---

### [SR-20260610-005] [LOW] .claude/skills/post-new/09-review.md — --version-history flag has no handler in post-review

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Add flag support or use different mechanism.

---

### [SR-20260610-006] [LOW] .claude/skills/post-review/SKILL.md — Workflow in allowed-tools may not be valid

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Verify Workflow tool name or use Bash instead.

---

### [SR-20260610-007] [MEDIUM] .claude/skills/post-new/SKILL.md — Blockquote breaks markdown table

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Move note outside table.

---

### [SR-20260610-008] [MEDIUM] .claude/skills/post-new/08-user-review.md — Duplicate: image manifest path mismatch

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Same as SR-003.

---

### [SR-20260610-009] [MEDIUM] .claude/skills/post-new/09-review.md — Claims 3 models but default is 2

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Update to reflect current 2-model default.
