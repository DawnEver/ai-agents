---
name: sharp-review-2026-06-22
description: Sharp review findings — 17 total
metadata:
  type: project
---

## Review 2026-06-22 (session) — architecture survey (架构锐评)

### Reviewer Status
- Reviewer A (Codex): skipped
- Reviewer B (DeepSeek): OK
- Reviewer C (Opus): OK

### Resolution (2026-06-23)

All 17 findings fixed in one SSOT-consolidation pass:

- **SSOT (SR-003/004/010/013/014/015):** `AGENT.md` is now the single source of truth — added a
  Reference section defining directory layout, naming, the canonical glob set, meta.md schema,
  diff learning, style, and desensitization. `reply-email.md` and `archive.md` are procedural glue
  that reference it; no convention is restated. Step-number drift removed (sub-skills referenced by
  name, not number).
- **meta.md schema (SR-001/015):** canonicalized to `subject/sender/date/[recipient]/thread/round/prev`
  matching the actual corpus (`round:`, not the template's `position:`). Fixed the non-conforming
  2026-06-23 round meta.
- **Naming (SR-002):** documented the `-r<N>` same-date-round suffix convention and folded it into globs.
- **Stale memory (SR-005):** `thread-archive-prev-link.md` updated to the nested layout + `-rN`.
- **Desensitization (SR-006):** added `.claude/hooks/check-pii.sh` + installed git `pre-commit`;
  allowlisted `.claude/hooks/` in the parent `.gitignore`. Tested pass/fail.
- **File-split over-engineering (SR-008):** merged `continue-thread.md` + `style-learning.md` into
  `reply-email.md`; deleted both.
- **Layer separation (SR-007):** AGENT.md split into Workflow + Reference.
- **Audit trail (SR-011):** added `## Last checked` to `style/profile.md`.
- **Stale sharp-review snapshots (SR-012/016):** deleted `.claude/sharp-review/2026-06-0{4,5}.md`.
- **CLAUDE.md hop (SR-009):** rationale for the `@AGENT.md` include documented in AGENT.md (parent
  multi-project tree composes specs uniformly) — kept by design.
- **Glob scalability (SR-017):** documented as a known limitation with the `prev:`-chain escape hatch.

### Confirmed findings

---

### [SR-20260622-001] [HIGH] .claude/commands/reply-email/archive.md — meta.md frontmatter field mismatch: archive.md template says `position:` but actual meta.md files use `round:`

- **Category:** Bug
- **Status:** RESOLVED (2026-06-23)
- **Confidence:** single-reviewer
- **Suggestion:** Rename the template field to `round:` in archive.md to match actual practice, or rename all meta.md files to use `position:`.

archive.md line 36 generates `position: <N>` but meta.md files written since 2026-06-05 use `round: <N>`. Spec and actual behavior have diverged — any agent reading archive.md for the template produces meta.md inconsistent with the existing corpus.

---

### [SR-20260622-002] [HIGH] AGENT.md — Archive directory naming drifts from spec: AGENT.md prescribes `<topic>/` per round, but multi-round same-date threads use `-r2`...`-r5` suffixes

- **Category:** Bug
- **Status:** RESOLVED (2026-06-23)
- **Confidence:** single-reviewer
- **Suggestion:** Document the `<topic>-r<N>` suffix convention in AGENT.md and all glob patterns, or embed round into the date path.

Same-date rounds (e.g. torque-correlation-check -r2/-r3 on 2026/06/05) would collide without suffixes, but AGENT.md steps 2/4, continue-thread.md, and reply-email.md all assume `<topic>` alone is a stable directory name. The `-rN` convention is undocumented ad-hoc behavior.

---

### [SR-20260622-003] [HIGH] .claude/commands/reply-email.md — Archive glob patterns have inconsistent wildcard depth across reply-email.md, continue-thread.md, and style-learning.md — same layout, three representations

- **Category:** Bug
- **Status:** RESOLVED (2026-06-23)
- **Confidence:** single-reviewer
- **Suggestion:** Define the archive layout glob once in AGENT.md and have all command files reference it; never inline a glob in a command file.

reply-email.md: `archived/*/*/*/<topic>/` + `archived/*/<topic>/`. continue-thread.md: same counts. style-learning.md: `archived/*/*/*/*/reply.md` + `archived/*/*/reply.md`. Three files describe the same physical layout differently — a guaranteed SSOT drift hazard when the layout changes.

---

### [SR-20260622-004] [MEDIUM] AGENT.md — Heavy duplication: workflow steps, directory structure, meta.md fields, and diff-learning rules appear in AGENT.md, reply-email.md, and archive.md

- **Category:** Bug
- **Status:** RESOLVED (2026-06-23)
- **Confidence:** single-reviewer
- **Suggestion:** Make AGENT.md the single SSOT for reference material; trim command files to only procedure glue (bash commands, decision branches).

Directory structure diagram appears in both AGENT.md and archive.md; diff-learning rules appear near-verbatim in both. Every rule edit requires N-file synchronization — the 2026-06-09 final.md->reply.md rename touched AGENT.md, reply-email.md, AND archive.md.

---

### [SR-20260622-005] [MEDIUM] .claude/memory/2026/06/09/thread-archive-prev-link.md — Stale memory file describes flat archive layout `archived/YYYY-MM-DD/<topic>/` but actual structure is nested `archived/YYYY/MM/DD/<topic>/`

- **Category:** Bug
- **Status:** RESOLVED (2026-06-23)
- **Confidence:** single-reviewer
- **Suggestion:** Update the memory entry to the current nested layout, or prune it — AGENT.md is authoritative.

Any agent loading this memory entry as context gets wrong path instructions inconsistent with the post-refactor nested layout.

---

### [SR-20260622-006] [MEDIUM] AGENT.md — Desensitization rules are a doc-only convention — no hook, script, or CI check enforces PII absence in committed files

- **Category:** Feature
- **Status:** RESOLVED (2026-06-23)
- **Confidence:** single-reviewer
- **Suggestion:** Add a pre-commit hook that greps committed files for email-address patterns, deny-listed names, and reference-number patterns.

The only safeguard against committing PII is a human reading the rules. Real names and addresses live in gitignored files (correct), but nothing prevents accidental commits of tracked files containing them.

---

### [SR-20260622-007] [LOW] AGENT.md — AGENT.md (90 lines) interleaves runtime workflow steps with static reference material with no layer separation

- **Category:** Feature
- **Status:** RESOLVED (2026-06-23)
- **Confidence:** single-reviewer
- **Suggestion:** Split into a short workflow section at top (<40 lines) and a reference section (directory layout, style guidelines, desensitization) below.

Lines mix procedural steps, structural reference (dir layout), behavioral guidelines, and policy. An agent reading end-to-end must mentally re-sort the layers.

---

### [SR-20260622-008] [LOW] .claude/commands/reply-email/ — 5-file progressive-disclosure split for ~280 total lines is over-engineered — continue-thread.md (26 lines) and style-learning.md (20 lines) are too small to justify the file hop

- **Category:** Feature
- **Status:** RESOLVED (2026-06-23)
- **Confidence:** single-reviewer
- **Suggestion:** Merge continue-thread.md and style-learning.md inline into reply-email.md; keep only archive.md and reply-style.md as separate sub-skills.

continue-thread.md is one rule plus a bash one-liner; style-learning.md is a 3-step list. The indirection costs a file read for content that fits in a few bullets inline.

---

### [SR-20260622-009] [LOW] CLAUDE.md — CLAUDE.md is a 1-line `@AGENT.md` redirect — an unnecessary file hop in a single-project repo

- **Category:** Feature
- **Status:** RESOLVED (2026-06-23)
- **Confidence:** single-reviewer
- **Suggestion:** Inline AGENT.md into CLAUDE.md, or document the rationale for the `@AGENT.md` include pattern.

The include pattern helps in monorepos sharing a central AGENT.md; in a single-project repo it pays two file reads for one document.

---

### [SR-20260622-010] [LOW] .claude/commands/reply-email.md — Thread-linkage globs given as raw prose in reply-email.md but as full `ls -d ... 2>/dev/null` commands in continue-thread.md and style-learning.md

- **Category:** Bug
- **Status:** RESOLVED (2026-06-23)
- **Confidence:** single-reviewer
- **Suggestion:** Standardize: all three files give raw globs, or all three give complete ls invocations.

reply-email.md forces the agent to infer command usage from prose globs while the sub-skills give copy-pasteable commands — subtle inconsistency adding per-file cognitive friction.

---

### [SR-20260622-011] [INFO] style/profile.md — Style profile last-updated 2026-06-04 with later archived replies — no way to distinguish 'checked, nothing to update' from 'forgot to check'

- **Category:** Feature
- **Status:** RESOLVED (2026-06-23)
- **Confidence:** single-reviewer
- **Suggestion:** Add a `## Last checked` field updated on every archive step, separate from `## Last updated` (only changes when patterns are promoted).

Later rounds had no diff changes, so the profile may be correct, but there is no audit trail proving the diff-learning step ran.

---

### [SR-20260622-012] [INFO] .claude/sharp-review/2026-06-04.md — Sharp-review archive contains cross-project findings (manuscript-review, ai-post) that belong in the parent repo, not reply-email

- **Category:** Feature
- **Status:** RESOLVED (2026-06-23)
- **Confidence:** single-reviewer
- **Suggestion:** Filter sharp-review archives to reply-email-scoped findings; move cross-project findings to the parent repo's .claude/sharp-review/.

Roughly half the findings in this file concern other projects, making it misleading for anyone auditing reply-email's review history.

---

### [SR-20260622-013] [HIGH] AGENT.md — Workflow/structure/conventions fully duplicated between AGENT.md and .claude/commands/reply-email.md — two sources of truth that already drift (AGENT.md numbers workflow 1–7 with 7a–7e; reply-email.md numbers 1–9, and archive.md cross-references 'step 9' which doesn't exist in AGENT.md)

- **Category:** Bug
- **Status:** RESOLVED (2026-06-23)
- **Confidence:** single-reviewer
- **Suggestion:** Make AGENT.md the single canonical spec and have command files reference it instead of re-stating the workflow; align step numbering everywhere

AGENT.md §Workflow, §Directory structure, §File Conventions all restate what reply-email.md and archive.md restate again. Any change must be made in 2–3 places. The step-number mismatch (7 vs 9) is concrete evidence the duplication has already diverged.

---

### [SR-20260622-014] [HIGH] .claude/commands/reply-email/continue-thread.md — The fragile archive glob convention is hand-copied into 4 files with mutually inconsistent patterns — reply-email.md, continue-thread.md, and style-learning.md each use different glob depths

- **Category:** Bug
- **Status:** RESOLVED (2026-06-23)
- **Confidence:** single-reviewer
- **Suggestion:** Define the canonical nested + legacy-flat globs once in AGENT.md and reference them; normalize the three glob dialects to one

Because the YYYY/MM/DD-nested vs legacy-flat path layout is a cross-cutting convention, scattering it invites the subtle mismatch already present — style-learning.md globs to reply.md depth differently than continue-thread.md globs to directory depth, so a legacy flat archive could be found by one routine and missed by another.

---

### [SR-20260622-015] [MEDIUM] .claude/commands/reply-email/archive.md — meta.md schema diverges between archive.md (subject/sender/date/thread/position/prev) and AGENT.md step 7e (subject/sender/date/summary + prev, no thread/position)

- **Category:** Bug
- **Status:** RESOLVED (2026-06-23)
- **Confidence:** single-reviewer
- **Suggestion:** Pick one meta.md schema, define it in a single place (archive.md is the natural owner), and have AGENT.md link to it rather than partially redescribe it

AGENT.md describes meta.md as 'subject, sender, date, summary; prev: link; diff observations' while archive.md mandates YAML front-matter with thread + position fields. A reader following AGENT.md alone produces a non-conforming meta.md.

---

### [SR-20260622-016] [LOW] .claude/sharp-review/2026-06-04.md — Stale sharp-review snapshots (2026-06-04, 2026-06-05) linger alongside newer memory entries (2026-06-09), an apparent dead/superseded subsystem

- **Category:** Feature
- **Status:** RESOLVED (2026-06-23)
- **Confidence:** single-reviewer
- **Suggestion:** Archive or delete superseded sharp-review files once their findings are folded into memory, so the review trail has one current state

Two dated review files plus two later-dated memory entries suggest review output accumulating without an eviction policy; clarify whether sharp-review/ is an active log or transient scratch.

---

### [SR-20260622-017] [INFO] AGENT.md — Thread reconstruction relies entirely on filesystem globbing with no index; fine at current scale but O(n) directory scans grow with archive size

- **Category:** Performance
- **Status:** RESOLVED (2026-06-23)
- **Confidence:** single-reviewer
- **Suggestion:** If archives grow large, add a lightweight per-thread index (or make the prev: chain authoritative) instead of globbing all of archived/* every continuation

Every continuation re-globs the whole archive tree and reads up to N original.txt/reply.md pairs. Acceptable now (prompt-only project, small corpus); noted as the main scalability limit of the slug-as-key design.
