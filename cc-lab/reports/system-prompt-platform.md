# Self-Maintained System-Prompt Platform — research & design (2026-08-09)

**Goal:** a single, self-maintained system prompt used by every non-native path
(fabric providers incl. codex — "ccc/ccds 等"), while native `claude` keeps the
official prompt. Multiple switchable styles (coding / academic / post), extensible,
with a mechanism to track official Claude Code prompt updates.

## Verified mechanisms (tap capture, vanilla api.anthropic.com, haiku 4.5)

### 1. `claude -p --system-prompt "<static>"` — the cache key
- Static text enters the system head block; cross-process requests hit the server
  cache fully: first process creates 6,379, the next reads 25,752 / creates 0;
  a different static prompt drops back to 19,373 + 6,379 (measured repeatedly).
- Request structure (from tap): `system[billing][base][your static text]` +
  `user[CLAUDE.md/rules/memory ~6k][prompt w/ cache_control]` + `tools ~36k`.
  The static block + CLAUDE.md/rules + tools are byte-stable → full hits.
- 3-turn static-prompt loop ≈ $0.005 vs TUI $0.029 / default -p $0.043.
- `--system-prompt-file` exists (help: `--system-prompt[-file]`), so no shell
  quoting of big files.
- `--append-system-prompt` is useless for caching (sits past the byte-unstable
  tail); must REPLACE.

### 2. output-style does NOT inject under `--system-prompt`
- With `outputStyle: "academic"` in settings + `--system-prompt`, the system
  blocks are only [billing][base][static text] — no academic content. The official
  style mechanism is bypassed by full replacement.
- → styles must live INSIDE the self-maintained prompt files (one complete prompt
  per style). Official output-style keeps working for native claude (unaffected).
- Official behavior (docs): styles are appended to the END of the system prompt
  (no cache benefit past the dynamic tail); `/output-style` removed in v2.1.91;
  styles are baked once at session start (stable for caching).

### 3. codex `model_instructions_file` — replaces the built-in base prompt
- `codex exec -c model_instructions_file=<abs path>` (or `~/.codex/config.toml`)
  REPLACES the default base instructions entirely. Verified live: a marker file
  was echoed back by the model; built-in instructions gone.
- AGENTS.md (global `~/.codex/AGENTS.md` + project walk) still appends context on
  top — hierarchy: user message > developer > AGENTS.override.md > AGENTS.md >
  config user_instructions > model_instructions_file.
- codex side keeps its own project instructions separate → same single prompt text
  for claude and codex, different injection point.

### 4. official `--exclude-dynamic-system-prompt-sections` (claude 2.1.226)
- Moves per-machine sections (cwd, env info, memory paths, git status) from the
  system prompt into the first user message — "improves cross-user prompt-cache
  reuse". This is Anthropic's own fix for the byte-unstable tail we measured.
- **Ignored with `--system-prompt`** — our replace approach sidesteps it anyway.
  Useful for the native-claude path (which keeps the official prompt).

## Design

```
Sync/claude/system-prompt/           (in the existing config repo)
├── base.md                          # shared: identity, tool discipline, workflow
├── styles/
│   ├── coding.md                    # default coding mode
│   ├── academic.md                  # migrate output-styles/academic.md
│   ├── post.md                      # migrate ai-post/.claude/output-styles/post.md
│   └── <new>.md                     # extensible
├── build.mjs                        # base + style → dist/<style>.claude.md /
│                                    #   dist/<style>.codex.md (same text, two builds)
├── validate.mjs                     # static-ness check (no cwd/env/gitStatus leaks)
└── CHANGELOG.md                     # official-update absorption log
```

Injection points:
- fabric `spawnChild` (all providers): pass `--system-prompt-file
  dist/<style>.claude.md` (constant per style); history stays on stdin. Providers
  default to style `coding` unless overridden (profile / env / per-call).
- native claude TUI: no flag → official prompt (per user constraint).
- codex: `model_instructions_file = dist/<style>.codex.md` (config.toml or `-c`);
  project AGENTS.md keeps working on top.

Style switching = selecting the file → each style is its own stable cache key
(cross-process hits within a style; switching costs one cold call for that style).

Official-update tracking: full replacement makes runtime immune to official prompt
changes; watch/fork Piebald-AI/claude-code-system-prompts (npm-extracted, changelog
across 252 versions) as the change radar; `sync-official.mjs` diffs our sections
against the new official ones and produces an absorption list into CHANGELOG.md
(human-confirmed, not automatic).

## Open items
- Does `model_instructions_file` also get cross-process cache reuse (codex side)?
  Likely yes (stable instruction text), not measured — codex pricing is opaque.
- `--system-prompt-file` behavior parity with `--system-prompt` (assumed identical).
- native-claude path: consider `--exclude-dynamic-system-prompt-sections` in
  settings to improve the TUI's own cache behavior (separate concern).
