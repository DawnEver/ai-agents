---
name: system-prompt-platform
description: Self-maintained system prompt platform — verified --system-prompt cache mechanics, output-style bypass under replace, codex model_instructions_file replaces built-in base, official exclude-dynamic flag
created: 2026-08-09
tags: [system-prompt, cache, output-style, codex, fabric, design]
---

# Self-maintained system-prompt platform (2026-08-09)

Goal: every non-native path (fabric providers incl. codex) uses ONE self-maintained
system prompt with switchable styles (coding/academic/post + extensible); native
`claude` keeps the official prompt. Full design + data:
`reports/system-prompt-platform.md`.

## Verified (tap, vanilla api.anthropic.com, haiku 4.5)
1. **`claude -p --system-prompt "<static>"`** = cache key: static text in system
   head → cross-process full hits (first process create 6,379; next reads
   25,752/creates 0; different prompt → 19,373+6,379). Request structure:
   system[billing][base][static] + user[CLAUDE.md/rules ~6k][prompt+cache_control]
   + tools ~36k. `--system-prompt-file` exists. `--append-system-prompt` useless
   (past the unstable tail). 3-turn static -p ≈ $0.005 vs TUI $0.029 / default
   -p $0.043.
2. **output-style does NOT inject under `--system-prompt`** (settings
   outputStyle:"academic" + replace → system = 3 blocks, no style text). Styles
   must live inside our prompt files (one complete file per style). Official
   styles append at END of system prompt (no cache benefit), baked at session
   start; `/output-style` removed v2.1.91.
3. **codex `model_instructions_file`** (config.toml or `-c`) REPLACES the built-in
   base instructions entirely (marker echo verified live). AGENTS.md still appends
   on top (hierarchy: user > developer > AGENTS.override > AGENTS.md >
   user_instructions > model_instructions_file). Same prompt text for claude &
   codex, different injection point.
4. **official `--exclude-dynamic-system-prompt-sections`** (2.1.226): moves cwd/env/
   memory-paths/git-status out of system into first user message — Anthropic's own
   fix for the unstable tail we measured. Ignored with --system-prompt; relevant
   for the native-claude path.

## Design (Sync/claude/system-prompt/)
- base.md + styles/{coding,academic,post,...}.md → build.mjs → dist/<style>.claude.md
  + dist/<style>.codex.md (same text). validate.mjs checks static-ness (no
  cwd/env/git leaks). CHANGELOG.md for official-update absorption.
- fabric spawnChild: `--system-prompt-file dist/<style>.claude.md` constant per
  style; history on stdin; default style coding, overridable.
- codex: model_instructions_file = dist/<style>.codex.md; AGENTS.md keeps working.
- Native claude: official prompt (no flag).
- Official-update tracking: full replacement → runtime immune; Piebald
  (claude-code-system-prompts) as change radar; sync-official.mjs diffs → human
  absorption list.

## Injection composition (tap, cold-B T1)
~42.3k total = tools schema 33.6k (80%, Workflow 21.3k chars / Bash 11.7k / PS 9.2k /
DesignSync 8.9k / Agent 8.8k) + system text ~4.3k + first-user-message CLAUDE.md
~4.3k. `--allowedTools` does NOT shrink schema; **`--tools <subset>` DOES** (verified:
Bash,Read,Write,Edit,Glob,Grep → 21 defs ≈ 8k tok, −76%; fabric MCP auto-attached).
Third cost lever. Output-style discovery mirrors official paths (user/project/plugin
output-styles/, nearest wins, frontmatter name/description) — discover-styles.mjs
reads in place, existing config untouched; build = base.md + style body. Group E
(background/subagent/team) explicitly user-reviewing — not touched.

## base.md v1 (2026-08-09, Sync/claude/system-prompt/base.md, committed)
~1,500 tok, 7 sections modeled on official block2 structure. **Layer
separation**: base.md = system-level behavior only; user prefs (language/TDD/
git/rem memory) stay in global+project CLAUDE.md (injected on every path) —
5 overlaps removed, referenced not restated. Tool presets (exec 6,076 tok /
coord 7,674 / daily 16,436 / full 33,600). Smoke-tested: --system-prompt-file
base.md --tools <daily> → system 1,539 tok; run 2 = 50,848 read / 354 create
(full cross-process hit). Removed tools named as absent in base.md.

## Open items
- codex cross-process cache under model_instructions_file (not measured).
- --system-prompt-file parity with --system-prompt (assumed).
- native TUI cache: consider exclude-dynamic flag in settings.
