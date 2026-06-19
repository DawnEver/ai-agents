---
name: sharp-review-2026-06-19
description: Sharp review findings — 10 total
metadata:
  type: project
---

## Review 2026-06-19 (session) — security audit (安全锐评)

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): OK
- Reviewer C (Opus): skipped

### Confirmed findings

---

### [SR-20260619-001] [MEDIUM] ai-post/.claude/skills/post-new/01-clone.md — User-supplied slug used unsanitized in mkdir path construction, enabling path traversal

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Validate slug against a strict allowlist (e.g., `^[a-z0-9-]+$`) before interpolating into filesystem paths

The slug parameter is user-controlled (exposed via argument-hint: <slug> [platform]) and is directly interpolated into `mkdir -p "ongoing/<slug>/1-research" ...`. A slug like `../../etc/evil` or `../../.ssh` would traverse outside the intended `ongoing/` directory, allowing writes or reads in parent directories. Escaping with quotes mitigates command injection but does NOT prevent path traversal since `..` sequences are valid filesystem path components resolved by mkdir itself.

---

## Review 2026-06-19 (session) — architecture survey (架构锐评)

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): OK
- Reviewer C (Opus): skipped

### Confirmed findings

---

### [SR-20260619-002] [HIGH] .claude/agents/_writer-base.md + .claude/agents/*-writer.md — Template-loading preamble duplicated across _writer-base.md and all 4 platform writer agents

- **Category:** Feature
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Remove template-loading instructions from individual agents; let _writer-base.md Step 2 be the single source that all agents delegate to

_writer-base.md Step 2 ('Load Rules') tells writers to read templates/<platform>.md, _writing-craft.md, and _platform-registry.md. But every platform agent (xiaohongshu-writer.md, wechat-writer.md, zhihu-writer.md, twitter-writer.md) ALSO explicitly lists these same three Read instructions in its own body. If _writer-base.md is truly the shared Workflow, the individual agents should only define platform-specific pre-writing steps and then delegate — not re-declare the shared steps.

---

### [SR-20260619-003] [HIGH] templates/_writing-craft.md — 162-line monolithic file bundling 5+ distinct concerns

- **Category:** Feature
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Split into focused sub-files: _voice.md (identity+humor+rhythm), _transitions.md (connectives+scene-chaining), _anti-ai.md (banned phrases+replacement table+grading), keeping _writing-craft.md as the index

Every platform template loads the entire file. Twitter (English-only) gets Chinese connective tables it cannot use. Xiaohongshu (1000-char limit) gets paragraph mini-thesis and 3-pass review designed for 4000-char articles. The file has no internal sectioning that allows a writer to load only the parts it needs.

---

### [SR-20260619-004] [HIGH] .claude/skills/post-archive/SKILL.md — 221-line monolithic skill file; AGENT.md acknowledges decomposition is 'pending'

- **Category:** Feature
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Decompose into 0X-*.md sub-files matching the post-new/post-review progressive-disclosure pattern

post-new and post-review use SKILL.md as map + 0X-*.md as playbook. post-archive and post-publish are the old single-file pattern. This inconsistency is acknowledged in AGENT.md but not yet addressed.

---

### [SR-20260619-005] [MEDIUM] .claude/skills/post-publish/export_article.py — Python script imports python-docx with no requirements.txt or pip install instruction

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Add requirements.txt with python-docx pin, or add a pip install fallback in the pre-check step

export_article.py imports `from docx import Document`. post-publish SKILL.md Step 4 runs a pre-check for docx but only warns about the missing dependency — never tells the user HOW to install it. No requirements.txt, no setup.py, no pip command anywhere in the codebase.

---

### [SR-20260619-006] [MEDIUM] .claude/skills/post-publish/ — Python executables (export_article.py, char_count.py) co-located with markdown instruction files

- **Category:** Feature
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Move Python scripts to a top-level scripts/ or tools/ directory; keep .claude/skills/ for markdown instructions only

The skills directory is conceptually for slash-command definitions. Having executable Python scripts here breaks the pattern.

---

### [SR-20260619-007] [MEDIUM] templates/xiaohongshu.md, wechat.md, zhihu.md, twitter.md — Each platform template duplicates an identical ~12-line 'Writing Quality' section listing _writing-craft.md techniques

- **Category:** Feature
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Replace each duplicated block with a single reference line to _writing-craft.md

All 4 platform templates have a 'Writing Quality' section listing the same techniques from _writing-craft.md. When a new technique is added, all 4 templates must be updated. The list has already diverged (Twitter's version is abbreviated).

---

### [SR-20260619-008] [MEDIUM] .claude/agents/zhihu-writer.md — Has a '## 生成後報告' post-generation section with detailed metrics that the other 3 writer agents lack

- **Category:** Feature
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Move the post-generation report format into _writer-base.md Step 6 as a shared template

_writer-base.md Step 6 ('Report') is generic. zhihu-writer.md extends this with specific metrics and a publish recommendation. The other three agents have no post-generation report section at all.

---

### [SR-20260619-009] [LOW] .claude/agents/_writer-base.md — Has full agent YAML frontmatter but marked 'not directly invocable'

- **Category:** Bug
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Remove the YAML frontmatter block from _writer-base.md or harden against accidental invocation

The file has standard agent frontmatter (name, description, allowed-tools). The `_` prefix convention may not prevent the harness from registering it. If invoked directly, it would produce broken output without platform-specific rules.

---

### [SR-20260619-010] [LOW] templates/market-research-template.md — Template exists but is not explicitly loaded by any skill step or agent

- **Category:** Feature
- **Status:** FIXED
- **Confidence:** single-reviewer
- **Suggestion:** Either wire it into the post-new research step or remove it

The template defines a market-research structure but no skill or agent references it. Dead code that creates confusion about whether market research is standardized or ad-hoc.