---
name: sharp-review-2026-06-09
description: Sharp review findings — 24 total
metadata:
  type: project
created: 2026-06-09
accessed: 2026-06-09
tier: short
---




## Review 2026-06-09 (session) — current branch

### Reviewer Status
- Reviewer A (Codex, via takeover): OK
- Reviewer B (DeepSeek, via takeover): OK
- Reviewer C (Claude, native): OK

### Confirmed findings

---

### [SR-20260604-001] [MEDIUM] reply-email/.claude/commands/reply-email.md — Template path in meta.md example uses `../../` relative path which assumes exactly two levels of nesting — may be wrong for first-round archives

- **Category:** Bug
- **Module:** reply-email command
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Document that `prev:` path is relative to the current archive folder; clarify it is always `../../<YYYY-MM-DD>/<topic>` (two levels up from `archived/<date>/<topic>/`).

---

### [SR-20260604-002] [MEDIUM] reply-email/.gitignore — Narrowing `!.claude/memory/` to `!.claude/memory/tasks/` will untrack existing memory files outside `tasks/`

- **Category:** Bug
- **Module:** reply-email gitignore
- **Status:** FIXED
- **Suggestion:** Reverted to `!.claude/memory/` in this session.

---

### [SR-20260604-003] [LOW] ai-post/.claude/skills/post-new/06-images.md — Image output path mismatch between spawn prompt (`ongoing/<slug>/images/`) and template (`2-draft/images.md`)

- **Category:** Bug
- **Module:** post-new image workflow
- **Status:** OPEN
- **Suggestion:** Decide canonical location for image files and align all references.

---

### [SR-20260604-004] [LOW] ai-post/.claude/memory/.claude/rules/MEMORY.md — Misplaced file: memory index at wrong nested path

- **Category:** Bug
- **Module:** ai-post memory
- **Status:** OPEN
- **Suggestion:** Move to `ai-post/.claude/rules/MEMORY.md`.

---

### [SR-20260604-005] [LOW] ai-post/.claude/skills/post-new/06-images.md — Phase 2 confirmation prompt uses emoji (🖼️) conflicting with global no-emoji preference

- **Category:** Feature
- **Module:** post-new image workflow
- **Status:** OPEN
- **Suggestion:** Replace 🖼️ with plain text.

---

### [SR-20260604-006] [INFO] ai-post/README.md — README says `→ publish → archive` but these are separate user-invoked commands

- **Category:** Feature
- **Module:** ai-post docs
- **Status:** OPEN
- **Suggestion:** Clarify publish and archive are user-invoked.

---

### [SR-20260604-007] [INFO] reply-email/AGENT.md — File Conventions section still references `.txt` extensions

- **Category:** Bug
- **Module:** reply-email agent
- **Status:** FIXED
- **Suggestion:** Confirmed: File Conventions section does not list individual filenames — false alarm.

---

### [SR-20260604-008] [HIGH] reply-email/.gitignore — Memory files outside tasks/ are no longer committed

- **Category:** Bug
- **Module:** gitignore
- **Status:** FIXED
- **Suggestion:** Reverted to `!.claude/memory/` in this session.

---

### [SR-20260604-009] [MEDIUM] ai-post/.claude/memory/.claude/rules/MEMORY.md — Stray misplaced file under wrong nested path

- **Category:** Bug
- **Module:** memory system
- **Status:** OPEN
- **Suggestion:** Delete; canonical location is `ai-post/.claude/rules/MEMORY.md`.

---

### [SR-20260604-010] [MEDIUM] reply-email/.claude/commands/reply-email.md — .txt → .md migration already done this session

- **Category:** Bug
- **Module:** reply-email command
- **Status:** FIXED
- **Suggestion:** Migration complete — files renamed in this session.

---

### [SR-20260604-011] [MEDIUM] reply-email/AGENT.md — style/profile.md update buried as sub-bullet of thread-continuation note

- **Category:** Bug
- **Module:** reply-email agent
- **Status:** OPEN
- **Suggestion:** Move to a clearly numbered sub-step.

---

### [SR-20260604-012] [MEDIUM] ai-post/.claude/skills/post-new/06-images.md — Codex CLI pre-check assumes npm-global install

- **Category:** Bug
- **Module:** post-new images skill
- **Status:** OPEN
- **Suggestion:** Use `command -v codex` and provide fallback note.

---

### [SR-20260604-013] [LOW] ai-post/AGENT.md — Directory layout and template manifest path at different directory levels

- **Category:** Bug
- **Module:** ai-post agent docs
- **Status:** OPEN
- **Suggestion:** Align manifest path and image file path documentation.

---

### [SR-20260604-014] [LOW] reply-email/.claude/rules/MEMORY.md — Documents non-existent lifecycle scripts

- **Category:** Feature
- **Module:** memory system
- **Status:** OPEN
- **Suggestion:** Remove or add stubs.

---

### [SR-20260604-015] [LOW] ai-post/.claude/memory/tasks/archive/2026-06.md — Duplicate findings SR-20260606-005 and SR-20260606-016

- **Category:** Bug
- **Module:** task archive
- **Status:** OPEN
- **Suggestion:** Deduplicate.

---

### [SR-20260604-016] [INFO] ai-post/.claude/skills/post-new/06-images.md — Cost table redundantly repeats inline estimate

- **Category:** Feature
- **Module:** post-new images skill
- **Status:** OPEN
- **Suggestion:** Remove cost table or inline duplication.


## Review 2026-06-09 (follow-up)

## Review 2026-06-09 (session) — current branch

### Reviewer Status
- Reviewer A (Codex, via takeover): OK
- Reviewer B (DeepSeek, via takeover): OK
- Reviewer C (Claude, native): OK

### Summary
8 findings — all FIXED. Archive restructured to YYYY/MM/DD, original.txt for raw emails, prev: documented as cosmetic, diff -u for prose comparison.

---

### [SR-20260609-001] [HIGH] reply-email/.claude/commands/reply-email.md — Obsolete position format <N>/<M> in meta.md template contradicted new single-number position format

- **Category:** Bug
- **Module:** email reply workflow
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Changed position field to <N> only, consistent with prev-link threading model.

---

### [SR-20260609-002] [MEDIUM] reply-email/.claude/commands/reply-email.md — Archived directory retained final.md alongside reply.md — redundant copy

- **Category:** Feature
- **Module:** email reply workflow
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Removed final.md from archived structure; diff happens before mv final.md → reply.md.

---

### [SR-20260609-003] [MEDIUM] reply-email/AGENT.md — AGENT.md mirrored same final.md/reply.md duplication

- **Category:** Feature
- **Module:** email reply workflow
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Aligned AGENT.md with simplified layout: draft.md + reply.md only.

---

### [SR-20260609-004] [HIGH] .claude/commands/reply-email.md — final.md and reply.md byte-identical at archive time; cp created unnecessary duplicate

- **Category:** Bug
- **Module:** reply-email agent
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Changed archive step: diff first, then mv final.md reply.md (not cp).

---

### [SR-20260609-005] [MEDIUM] AGENT.md — Iteration loop removed in favor of user self-editing final.md

- **Category:** Feature
- **Module:** reply-email agent
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Confirmed user-directed design choice. User explicitly requested self-editing final.md over agent iteration. Diff learning accumulates improvements over time.

---

### [SR-20260609-006] [LOW] .claude/commands/reply-email.md — Bare diff command produced line-oriented output poorly suited for prose comparison

- **Category:** Bug
- **Module:** reply-email agent
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Changed to diff -u for unified diff context.

---

### [SR-20260609-007] [LOW] .claude/commands/reply-email.md — .md extension for plain-text emails may trigger unwanted Markdown rendering

- **Category:** Bug
- **Module:** reply-email agent
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Changed `original.md` → `original.txt` for raw incoming email. draft.md, final.md, reply.md remain .md (structured reply content).

---

### [SR-20260609-008] [LOW] .claude/commands/reply-email.md — prev: relative paths silently break if archive directories are reorganized

- **Category:** Bug
- **Module:** reply-email agent
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Documented in both AGENT.md and command file that prev: is cosmetic convenience; slug-based lookup (`archived/*/*/*/<topic>/`) is authoritative for thread reconstruction. Updated prev: examples to 4-level relative paths matching new `YYYY/MM/DD` structure.


## Review 2026-06-09 (follow-up)

## Review 2026-06-09 (session) — current branch

### Reviewer Status
- Reviewer A (Codex, via takeover): OK
- Reviewer B (DeepSeek, via takeover): OK
- Reviewer C (Claude, native): OK

### Summary
8 findings — all FIXED. Workflow refactor with archive path restructuring (YYYY/MM/DD), file extension cleanup, and diff learning mechanism.


## Review 2026-06-09 (follow-up)

## Review 2026-06-09 (follow-up) — progressive disclosure refactor

### Summary
7 findings. 3 FIXED (2 HIGH backward-compat, 1 MEDIUM resume clarity). 4 OPEN (false alarm, intentional design, accepted tradeoffs).
