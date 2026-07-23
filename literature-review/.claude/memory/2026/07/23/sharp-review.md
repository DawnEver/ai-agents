---
name: sharp-review-2026-07-23
description: Sharp review findings — 13 total
metadata:
  type: project
---


## Review 2026-07-23 (session) — docs review (文档锐评)

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): skipped
- Reviewer C (Opus): skipped

### Confirmed findings

---

### [SR-20260723-001] [HIGH] .claude/skills/manuscript-review/SKILL.md — The documented entrypoint `/manuscript-review:new` does not match the actual skill definition.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Either rename/add the real slash-command/skill entrypoint so `/manuscript-review:new` exists, or update all docs to the actual invocable command exposed by `name: manuscript-review`.

The repo has `.claude/skills/manuscript-review/SKILL.md` with frontmatter `name: manuscript-review`, but there is no `.claude/commands/manuscript-review/new.md` or equivalent command directory. README.md, AGENT.md, and the skill itself repeatedly document `/manuscript-review:new <pdf>`. As documented, a user will try a command that the checked-in skill layout does not prove exists.

---

### [SR-20260723-002] [HIGH] .claude/skills/manuscript-rerun/SKILL.md — The documented rerun command namespace does not match the actual skill name.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Make the rerun skill invocable as `/manuscript-review:rerun` via an actual command file/alias, or change docs to the real skill command name implied by `name: manuscript-rerun`.

The rerun skill frontmatter says `name: manuscript-rerun`, but its title and examples document `/manuscript-review:rerun`. README.md and AGENT.md repeat that command. There is no visible command directory wiring `manuscript-review:rerun` to this skill, so the docs describe an entrypoint that is not backed by the repo structure.

---

### [SR-20260723-003] [MEDIUM] .claude/skills/manuscript-rerun/SKILL.md — Rerun claims steps 2 and 4 work, but the tool allowlist omits `Workflow`.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add `Workflow` to the rerun skill `allowed-tools`, or document that workflow-backed steps must be rerun through the main orchestrator instead.

The examples explicitly include `/manuscript-review:rerun 2 ...`, and the text says rare earlier steps work. But step 02 invokes `manuscript-review-literature` via `Workflow`, and step 04 invokes `manuscript-review-fanout` via `Workflow`. The rerun skill allowlist is only `Read,Write,Bash,Glob,Grep,Agent,Skill`, so the documented rerun path cannot execute those workflow-backed steps as written.

---

### [SR-20260723-004] [MEDIUM] .claude/skills/manuscript-review/08-archive.md — Archive step reads `archived/YYMMDD/<slug>/angles.md`, but the pipeline writes angles under `2-review/angles.md`.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Change the archive instructions to read `archived/YYMMDD/<slug>/2-review/angles.md`.

Step 03 outputs `ongoing/<slug>/2-review/angles.md`, the directory layout in README.md/AGENT.md places `angles.md` under `2-review/`, and step 08 moves the whole slug directory unchanged. After the move, the file is `archived/YYMMDD/<slug>/2-review/angles.md`, not `archived/YYMMDD/<slug>/angles.md`. The current instruction points at a path that will not exist.

---

### [SR-20260723-005] [LOW] AGENT.md — Setup wording says clone the ingest library 'alongside this repo' but the command and actual layout put it inside the repo root.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Clarify the intended layout: either say 'inside this repo root' or change the install command to the correct sibling path.

AGENT.md says `# Clone the ingest library alongside this repo`, then runs `git clone https://github.com/DawnEver/paper_pdf_ingest.git` and `pip install -e paper_pdf_ingest/` from the manuscript-review root. The actual repo contains `manuscript-review/paper_pdf_ingest/`, so 'alongside this repo' is misleading and conflicts with the relative install path.

---

### [SR-20260723-006] [INFO] README.md — No stale `paper-review`, `paper-rerun`, `paper_review`, `/paper-review:`, or `paper-review-fanout` references were found in active docs.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Leave `paper_pdf_ingest` references alone unless the ingest library itself is renamed; they match the actual `paper_pdf_ingest/` dependency and `scripts/ingest.py`.

A hidden grep over README.md, AGENT.md, CLAUDE.md, `.claude/skills`, `.claude/workflows`, `.claude/agents`, templates, and scripts found old-name hits only for `paper_pdf_ingest` and historical memory entries. The active workflow filenames are `.claude/workflows/manuscript-review-literature.js` and `.claude/workflows/manuscript-review-fanout.js`, matching the active skill docs.


## Review 2026-07-23 (follow-up)

## Review 2026-07-23 (session) — adversarial review (对抗性审查) + diff review

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): skipped
- Reviewer C (Opus): OK

### Confirmed findings

---

### [SR-20260723-007] [HIGH] manuscript-review/.claude/skills/manuscript-review/SKILL.md — The rename strands existing untracked review state because resume only looks under the new project path.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add an explicit migration step/check for legacy `paper-review/ongoing` and `paper-review/archived`, or keep a compatibility command that can locate and migrate/copy old slugs before resuming.

The pipeline now documents `/manuscript-review:new <slug>` and searches only `ongoing/<slug>/` and `archived/*/<slug>/` inside `manuscript-review`. But the actual review artifacts (`ongoing/`, `archived/`, raw PDFs, generated critique files) are typically gitignored runtime state. A user pulling this rename will get tracked files in `manuscript-review/`, while their untracked `paper-review/ongoing` may remain outside the new project. The resume table then reports `nothing` and can start a duplicate run instead of resuming the existing manuscript review.

---

### [SR-20260723-008] [MEDIUM] manuscript-review/.claude/skills/manuscript-rerun/SKILL.md — Deleting the old `paper-rerun` skill provides no compatibility path for existing command muscle memory, docs, or automation.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Keep a deprecated `paper-rerun` wrapper skill for one release that forwards users to `/manuscript-review:rerun`, or document the breaking command rename prominently with exact migration instructions.

The old skill is deleted and the new examples replace `/paper-review:*` with `/manuscript-review:*`. Any saved prompts, scripts, aliases, or memory instructions that invoke `/paper-review:rerun` now fail hard. The table labelled `Old call | Now` is also misleading: it maps old archive/repolish concepts after already renaming the namespace, but does not preserve or explain the actually removed `/paper-review:*` entry points.

---

### [SR-20260723-009] [MEDIUM] manuscript-review/.claude/skills/manuscript-review/01-ingest.md — The ingest step documents a renamed venv elsewhere but still runs ambient `python`, so dependency failures are left to luck.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Either invoke the documented venv interpreter explicitly, add a preflight that verifies `paper_pdf_ingest` and its dependencies under the interpreter being used, or change setup docs to require activating the venv before running the skill.

README/AGENT now tell users to create `~/.local/share/manuscript-review-venv`, but step 01 runs `python -m scripts.ingest ...`. That does not use the documented venv unless the shell is already activated. Worst case: users recreate the new venv exactly as instructed, then the pipeline still runs system Python and fails with missing `paper_pdf_ingest`, `pymupdf4llm`, or `marker-pdf`. The error template also points users at fixing the venv even though the command may not be using it.

---

### [SR-20260723-010] [LOW] manuscript-review/README.md — The README silently changes the clone URL to a new repository name without any fallback or migration note.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Confirm the `DawnEver/manuscript-review` remote exists and add a note for users of `DawnEver/paper-review` explaining whether the old repository was renamed, archived, or replaced.

The setup command now says `git clone https://github.com/DawnEver/manuscript-review.git`. If the remote rename has not happened, fresh installs fail immediately. If it has happened, existing users still need to know whether GitHub redirects the old URL and whether local remotes should be updated. The change assumes the external repository rename is already complete and stable but does not enforce or document that assumption.

---

### [SR-20260723-011] [LOW] manuscript-review/.claude/workflows/manuscript-review-fanout.js — Stale 'paper reviews' terminology in workflow description after rename

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Change description to 'Parallel fanout of manuscript reviews across multiple models'.

meta.name was correctly updated to 'manuscript-review-fanout', but line 3's description string still reads 'Parallel fanout of paper reviews'. Cosmetic only (description isn't a lookup key), but it's an incomplete rename that will show stale text in the /workflows list and permission dialog.

---

### [SR-20260723-012] [LOW] manuscript-review/.claude/skills/manuscript-rerun/SKILL.md — Skill folder/name 'manuscript-rerun' but every invocation is documented as '/manuscript-review:rerun' — possible namespace mismatch

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Verify command resolution: if prefix derives from plugin name (manuscript-review) and not folder name, this is fine; if not, rename folder or invocation strings.

The main skill uses folder 'manuscript-review' to '/manuscript-review:new', so prefix appears to track the folder name. By that pattern, folder 'manuscript-rerun' would resolve to '/manuscript-rerun:rerun', not the '/manuscript-review:rerun' documented. This mismatch predates the rename (old paper-rerun/ had the same shape), so it's likely a working plugin-namespace convention — but the rename was the moment to reconcile it.

---

### [SR-20260723-013] [INFO] manuscript-review/README.md — Renamed venv path in docs will orphan existing installs

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a one-line migration note, or leave as-is if only fresh installs are expected.

README.md:17 and AGENT.md:13 now reference '~/.local/share/manuscript-review-venv/'. Anyone who installed under the old 'paper-review-venv' path will follow these docs into a fresh install with no note that the old venv is now dead.
