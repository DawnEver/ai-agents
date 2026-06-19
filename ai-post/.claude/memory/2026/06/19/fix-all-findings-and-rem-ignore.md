---
name: fix-all-findings-and-rem-ignore
description: Cleared 68/69 sharp-review findings (decompositions, SSOT, slug sanitization, scripts/ move); rem scope-ignore must be configured at findProjectRoot level, plus two task-engine parsing gotchas
metadata:
  type: project
---

# Fix-all sharp-review pass + rem scope-ignore footgun

## What changed (ai-post)

Drove open sharp-review findings 69 → 1 in one session (parallel verify/fix subagents,
one per file-disjoint group). Substantive 2026-06-19 fixes:

- **Slug path-traversal** (`post-new/01-clone.md`): validate `<slug>` against `^[a-z0-9._-]+$`
  and reject `..` before any `mkdir`. Quoting stops injection but NOT `..` traversal.
- **Writer-agent dedup**: template-loading preamble now lives ONLY in `_writer-base.md` Step 2;
  the 4 platform agents delegate. Shared report format in Step 6. Removed YAML frontmatter
  from `_writer-base.md` (it's an include, not invocable).
- **`_writing-craft.md`**: kept as one file but added a top **Section Index** (which section
  applies to which platform) so writers load only what's relevant; the 4 platform templates
  now reference it instead of duplicating the Writing Quality block.
- **Progressive disclosure completed**: `post-archive` → `01–04`, `post-publish` → `01–03`
  sub-files (SKILL.md is now a map for every skill). AGENT.md "decomposition pending" note removed.
- **Scripts relocated**: `export_article.py` + `char_count.py` `git mv`'d to `scripts/post-publish/`
  with `requirements.txt` (python-docx pinned). New layout dir: `scripts/<skill>/`. The script's
  `__file__`-relative repo-root walk needed one fewer `.parent` after the move.
- **Schema SSOT**: finding JSON schema single-sourced in `post-review/01-identities.md`;
  `03-execution.md` references the named anchors, no inline literal.

Remaining open: **SR-20260611-001** (MEMORY.md shows only timestamps, no summaries). Proper fix
is a rem-engine change (derive index summary from each file's `description:` frontmatter) — and
rem lives in a gitignored cached clone, so a local edit wouldn't reach the installed plugin.

## rem `/todo` + scope-ignore gotchas (cc-market/rem)

- **Scope-ignore (方案 B) is read from `repoRoot`, not the project scope.**
  `resolveIgnore()` → `loadState()` → `stateFile = findProjectRoot()/.claude/.rem-state.json`.
  Here `findProjectRoot()` resolves to the **parent `agents/`** (that's also why `/todo`
  surfaces `../reply-email`), while `scopeRoot` (`findMemoryScope`, nearest `.claude/memory`)
  is `ai-post`. Configuring `scopes.ignore:["repos"]` in `ai-post/.claude/.rem-state.json`
  does nothing — it MUST go in `agents/.claude/.rem-state.json`. A bare pattern (no `/`)
  matches a directory basename at any depth, so `["repos"]` skips the whole `repos/` clone tree.
- **`SR_STATUS_RE` only matches `**Status:**` at line start.** Findings written inline as
  `- **Category:** Bug | **Status:** FIXED` parse as OPEN (status regex misses them). Keep
  `**Status:**` on its own line.
- **`mark <id> <status>` uses a non-global regex** → flips only the FIRST occurrence of a
  duplicated SR-ID in a file. Files that reuse IDs across review sessions (e.g. 06-11) need a
  direct edit of each block's Status line.

## Verification

Confirmed each "likely-resolved" finding against current code (the flag only means the cited
file's mtime > discovery date — NOT proof of fix). cc-market `watch` cooldown tests: 10/10 pass.
Python scripts `ast.parse` clean. State/`.rem-state.json` files are gitignored — nothing committed.
