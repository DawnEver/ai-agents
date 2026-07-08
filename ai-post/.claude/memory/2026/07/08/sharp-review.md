---
name: sharp-review-2026-07-08
description: Sharp review findings — 11 total
metadata:
  type: project
---

## Resolution 2026-07-08 (post-review triage)

Findings triaged against the source-generalization change (`feat(post-new)`: github/local-dir/local-file sources + `repo-*`→`source-*` rename):

- **FIXED (this change's own issues):**
  - SR-005 — AGENT.md line 25 rename miss → now `source (pointer), source-exploration, market-research, source-analysis, brief`.
  - SR-006 — 01-clone.md dead-code `|| resolved=` fallback → parent dir resolved + tested separately.
  - SR-007 — README `/post-new` command usage → shows `<github-url|local-path|slug> [platform]`.
  - SR-009 — cleanup others-detection: prefix glob + unescaped grep regex → exact slug-boundary `case` match.
  - SR-010 — cleanup: added symlink guard before `rm -rf repos/$repo_slug` (protect external source).
  - SR-011 — cleanup: `rm -rf "ongoing/<slug>"` → `rm -rf "ongoing/$slug"`.
- **FALSE POSITIVE (verified):**
  - SR-001 — wechat-writer.md frontmatter is clean (`platform: wechat` on its own line). Reviewer read-encoding artifact.
  - SR-002 — no mojibake on disk (grep for U+FFFD / mojibake sequences = 0). PowerShell/Codex read-encoding artifact.
- **OUT OF SCOPE (pre-existing, not this feature):** SR-003 (image-lifecycle template contradiction), SR-004 (dependency-docs completeness), SR-008 (post-publish supported-platforms formatting; likely same read artifact as SR-002).

## Review 2026-07-08 (session) — docs review (文档锐评)

### Reviewer Status
- Reviewer A (Codex): OK — agent-mode, full-repo exploration
- Reviewer B (DeepSeek): FAILED — agent-mode timed out (600s)
- Reviewer C (Opus): OK — review-mode over gathered rename/safety-critical context

### Confirmed findings

---

### [SR-20260708-001] [HIGH] .claude/agents/wechat-writer.md — The WeChat agent frontmatter is malformed, so the documented wechat-writer agent metadata does not match a valid agent definition.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Put platform: wechat on its own YAML line and repair the corrupted description text.

The description: line contains platform: wechat inline instead of a separate key. Any loader expecting frontmatter keys will treat the whole text as the description and fail to see the platform field, despite AGENT.md and templates/_platform-registry.md advertising wechat-writer as the WeChat platform agent.

---

### [SR-20260708-002] [HIGH] templates/*.md, .claude/agents/*.md, .claude/skills/**/*.md, scripts/post-publish/*.py — Large parts of the project documentation and embedded script messages are mojibake, making critical Chinese workflow rules unreadable or semantically broken.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer (LIKELY FALSE POSITIVE — verify encoding)
- **Suggestion:** Recover these files from a correct UTF-8 source or manually rewrite the corrupted text; then add an encoding check that rejects replacement/mojibake markers.

Examples include .claude/agents/xiaohongshu-writer.md, .claude/skills/post-review/SKILL.md, templates/_platform-registry.md, and script literals in scripts/post-publish/char_count.py / export_article.py. NOTE: this is most likely a PowerShell/Codex read-encoding artifact, NOT on-disk corruption — verify the actual working-tree encoding (e.g. `git show :<file> | file -`) before acting; if the tree is genuinely UTF-8 this finding is a false positive and should be closed.

---

### [SR-20260708-003] [MEDIUM] .claude/agents/_writer-base.md, templates/xiaohongshu.md, templates/wechat.md, templates/zhihu.md, .claude/skills/post-new/10-summary.md — The image lifecycle docs contradict each other about whether drafts should contain [IMAGE: ...] placeholders or final markdown image references.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Separate draft-stage and final-stage requirements explicitly in every platform template: v1 writers emit only [IMAGE: ...]; finalization replaces them with markdown refs.

_writer-base.md says v1 generation must use only [IMAGE: ...] placeholders and must not write markdown image references. But platform templates such as templates/zhihu.md, templates/wechat.md, templates/xiaohongshu.md still include output/checklist requirements for markdown refs like ![...](../../images/<id>-vN.png). A writer following both documents gets incompatible instructions.

---

### [SR-20260708-004] [MEDIUM] README.md, .claude/skills/post-review/SKILL.md, .claude/skills/post-review/02-reviewers.md — The review dependency documentation is incomplete and points at generic repositories instead of actionable plugin installation/setup instructions.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Document the exact required plugin names, install commands, expected MCP tool name, and expected merge-findings.js path; replace the generic GitHub links with the actual plugin references.

README.md says takeover and sharp-review are dependencies, but links both to https://github.com/anthropics/claude-code, which does not identify the cc-market plugins or how to install them. The skill then assumes mcp__plugin_takeover_takeover__call_model and a cached sharp-review/scripts/merge-findings.js. Setup docs do not tell a new user how to satisfy or verify these.

---

### [SR-20260708-005] [MEDIUM] ai-post/AGENT.md — Directory-layout line 25 still uses both pre-rename names repo-exploration and repo-analysis (rename miss).

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer (most on-target for the rename's consistency goal)
- **Suggestion:** Change line 25 to `1-research/       — source-exploration, market-research, source-analysis, brief` to match the renamed runtime artifacts.

The rename repo-exploration.md->source-exploration.md and repo-analysis.md->source-analysis.md was applied everywhere except the canonical Directory Layout in AGENT.md — the one place a contributor looks to learn artifact names. AGENT.md is the declared source of truth for layout, so this stale line contradicts SKILL.md's pipeline/resume tables (source-exploration.md / source-analysis.md). Confirmed by grep across the whole ai-post tree: this is the ONLY lingering old-name occurrence outside the deliberate SKILL.md legacy-fallback note (line 90) and the frozen memory entries.

---

### [SR-20260708-006] [MEDIUM] ai-post/.claude/skills/post-new/01-clone.md — Source resolver `|| resolved="$src_arg"` fallback is effectively dead code; a missing parent dir yields a garbage /basename path.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Resolve the dir separately and test it: `dir="$(cd "$(dirname "$src_arg")" 2>/dev/null && pwd)"; resolved="${dir:+$dir/}$(basename "$src_arg")"; [ -n "$dir" ] || resolved="$src_arg"`.

In `resolved="$(cd ... && pwd)/$(basename "$src_arg")" || resolved="$src_arg"`, the assignment exit status is that of the LAST command substitution — $(basename ...), which almost always succeeds — so the || fallback never fires. When cd $(dirname) fails (nonexistent parent), the first substitution is empty and resolved becomes `/<basename>`, a bogus path rooted at /. The -d/-f tests then fail and it exits 'Unrecognized source', which is tolerable, but the documented fallback semantics do not match the code. Confined to missing-parent inputs. (Slug traversal validation itself — lines 49-60 — is sound: rejects `..` and out-of-allowlist, and correctly exempts the source path.)

---

### [SR-20260708-007] [LOW] README.md, AGENT.md, .claude/skills/post-new/SKILL.md — Top-level command usage is stale/incomplete compared with the actual post-new skill arguments and resume behavior.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update README command examples to show /post-new <github-url|local-path|slug> [platform] and mention resume-by-slug behavior, matching .claude/skills/post-new/SKILL.md.

README.md documents /post-new <url> only, while the skill frontmatter and body support GitHub URLs, local paths, local files, existing slugs, and optional platform selection. AGENT.md has the richer source description, but README remains the likely first entry point and underspecifies supported usage.

---

### [SR-20260708-008] [LOW] .claude/skills/post-publish/SKILL.md — The Supported Platforms list is malformed, merging multiple bullets onto one line.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Put each platform on its own bullet and repair the corrupted Chinese labels.

The current section renders as - xiaohongshu ... - wechat ... - zhihu ... on one bullet line before Twitter. This makes the supported-platform list harder to scan and easier for agents to parse incorrectly. (May share root cause with the encoding artifact in SR-002 — verify.)

---

### [SR-20260708-009] [LOW] ai-post/.claude/skills/post-archive/04-cleanup.md — others-detection prefix glob "$repo_slug"* over-matches sibling slugs and injects raw slug into a grep regex.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Anchor to a real boundary: iterate `for d in ongoing/"$repo_slug"* archived/*/"$repo_slug"*; do case "${d##*/}" in "$repo_slug"|"$repo_slug"__*) ...; esac; done` and skip the current $slug by exact string compare, not grep -v with an unescaped regex.

Two non-catastrophic issues. (1) `ls -d ongoing/"$repo_slug"*` matches any sibling sharing the prefix (repo_slug foo matches foo-bar, foobar), so `others` gets false positives and the shared clone is retained when it could be freed — safe direction (cache leak, never a wrong delete). (2) `grep -v "/$slug\$\|/$slug/"` interpolates the slug straight into a BRE; slugs legally contain '.', which is regex any-char, so a.b would filter /axb. Because repo_slug scopes the eventual rm -rf, neither can delete another repo's cache.

---

### [SR-20260708-010] [LOW] ai-post/.claude/skills/post-archive/04-cleanup.md — The 'never delete the external source path' guarantee holds but rests on an implicit, unguarded invariant.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer (target-safety currently VERIFIED — this is hardening)
- **Suggestion:** State the invariant in a comment and add a defensive guard before the rm (e.g. refuse to rm if repos/$repo_slug is a symlink), so a future change that materializes repos/<repo-slug>/ as a real copy or symlink can't start deleting user-owned material.

Given the design (local-dir referenced in place -> only a .src pointer; local-file leaves nothing under repos/), the delete targets are repos/$repo_slug (absent for local sources -> no-op), repos/$repo_slug.src (the pointer, not its content), and the ongoing workspace — so target-safety currently holds and the prose is clear (the review's focus concern — cleanup never deleting an external path — is satisfied). Minor doc gap: cleanup claims a local-file 'leaves nothing under repos/', but a local-file reached via a user-created .src pointer would leave that pointer (harmlessly removed by rm -f).

---

### [SR-20260708-011] [LOW] ai-post/.claude/skills/post-archive/04-cleanup.md — Step 7 block mixes literal placeholder rm -rf "ongoing/<slug>" with real $repo_slug/$slug shell variables.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** For consistency use the real variable `rm -rf "ongoing/$slug"` in the executable block, matching the $repo_slug/$slug usage in the lines above it.

Surrounding lines dereference real variables (repos/$repo_slug, repos/$repo_slug.src, grep -v "/$slug..."), but the workspace-removal line reads `rm -rf "ongoing/<slug>"` with an angle-bracket placeholder. Across these skill docs <slug> is a documented template the agent substitutes, so this likely does not no-op at runtime — but mixing literal placeholders and live shell vars in one runnable block is an internal inconsistency that invites a copy-paste that silently fails to remove the workspace.
