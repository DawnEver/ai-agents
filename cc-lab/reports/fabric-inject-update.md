# fabric 0.1.17 injection chain — real-session verification (2026-08-10)

Case: `cases/fabric-inject-update.case.mjs`. Drives the UPDATED fabric engine
(plugin cache 0.1.17, then the fixed repo engine) through its own spawn paths —
`spawnChild` (stateless `claude -p`) and `openSession` (persistent PTY) — behind
the observe proxy (`CC_MARKET_SHARED` override). Evidence: `http.jsonl` captures
of real child requests to the real DeepSeek upstream (model remapped haiku →
`deepseek-v4-flash[1m]`).

## Verdict

The 2026-08-10 systematic layering works end-to-end in a real child — BUT the
0.1.17 release shipped with a broken stateless claude path (`--verbose` missing).
Found by this case, fixed in the repo, 317/317 tests green.

## Finding 1 (bug, fixed): stateless claude spawns exit 1 — `--verbose` missing

`engine/spawn-child.mjs` composed `claude -p <prompt> --output-format stream-json`
(and the stdin variant) WITHOUT `--verbose`. The CLI (2.1.226.9e0) hard-fails:

```
Error: When using --print, --output-format=stream-json requires --verbose
```

Both argv and stdin paths. `open-session.mjs` had already documented the
requirement ("--verbose is REQUIRED by the CLI for --print + stream-json output
(exit 1 without)") — the stateless engine never got it (`git log -S--verbose` is
empty for spawn-child.mjs). Since `spawnClaudeP` (every `fabric:call --provider
claude` / claude-mode task) delegates to `spawnChild`, **every stateless claude
call in the released 0.1.17 dies with exit 1**. DeepSeek/API providers are
unaffected (they don't use the CLI).

Fix: add `--verbose` to both arg compositions (`spawn-child.mjs:252-258`); tests
updated (`tests/spawn-child.test.mjs` slices 0-4/0-6 → 0-5/0-7). Its extra
system events on stdout are already skipped by `parseStreamJsonOutput`/`emitLine`.

## Finding 2: system prompt replacement verified (array form)

The child sends `system` as an ARRAY of 3 blocks: billing header
(`x-anthropic-billing-header: cc_version=...`) + SDK head ("You are a Claude
agent, built on Anthropic's Claude Agent SDK.") + **our platform file
(`# claude-base.md — claude platform base`)**. Official prompt ("agentic coding
tool") absent. Total request input: **30,257 tok** for the full 28-tool schema
(vs ~42.3k official injection on the old build — the new SDK head is one line).

## Finding 3: cross-process cache — per-provider reality

DeepSeek's anthropic-compat layer reports the cache fields but never engages
them for our blocks: runs A and B (byte-identical system, same cwd) both show
`cache_read 0 / cache_creation 0`, identical input 30,257 = 30,257. The
deterministic claim that DOES hold cross-process on deepseek: the per-run bill
is byte-identical (system byte-identical asserted). The cache-hit lever remains
a NATIVE-claude-upstream property (already measured: validate-cache.mjs 15.6k
read / 0 create). Open question: whether the new SDK CLI marks our file block
with `cache_control` on the native path (in captures the marker appeared only on
the SDK-head block) — worth re-verifying with `validate-cache.mjs` after the
plugin update.

## Finding 4: cost lever verified — toolsPreset trims the schema

`--tools=Bash,Read,Write,Edit,Glob,Grep` → `body.tools` = exactly 6 names,
input drops **30,257 → 7,770 (−74%)**. Both spawn paths honor it:
`spawnChild` via `extraArgs`, `openSession` via `profile.toolsPreset` (verified
on the persistent PTY session, E). The separate-arg `--tools <list>` form
(profileArgs) does NOT mis-parse in stdin mode (the argv-prompt pitfall does not
apply to the persistent path).

## Finding 5: style chain verified

`style: 'academic'` → `resolveStyleFile` auto-builds
`dist/academic.claude.md` from the platform dir → system = claude-base +
academic body ("You are a scholarly writing and thinking partner."). No manual
intervention; the full profile.style → dist → injection path works.

## Finding 6: mode layering verified — template in the USER message only

The real main turn's user message is 3 blocks: [0] agent-types reminder,
[1] claudeMd context, [2] mode template ("Identify root causes...") + prompt.
System stays platform-only (no template bleed). The guard test
(`prompts-overlap.test.mjs`) enforces the single-source rule.

## Finding 7: per-spawn request sequence (cost awareness)

A stateless spawn fires, in order: hello probe (404 on deepseek — harmless) →
(only in stdin mode) a **title-gen** `/v1/messages` call (tools: 0, system =
title instruction, user = `<session>` wrapper) → the real tool-bearing turn →
N agentic continuation turns if the model calls tools (observed 4 extra for
'Say OK.' — the model's own behavior, not an engine cost). Tool-bearing turns
are the right main-turn filter (`tools.length > 0`), same rule AGENTS.md
prescribes for tap records.

## Post-fix closure (0.1.18, 2026-08-10)

Full case re-run against the PLUGIN CACHE 0.1.18 (no CC_MARKET_SHARED override)
— all assertions pass. Live production check: `fabric:call --provider claude
mode=task` through the reloaded plugin MCP server (handleCall → layering →
spawnClaudeP → spawnChild) returns normally ("OK"). The stateless claude path
that exited 1 in 0.1.17 is confirmed working in the installed plugin.

## Harness notes (for future runs of this case)

- The observe proxy APPENDS to `http.jsonl` and restarts its id sequence per
  proxy start — a re-run against the same dir mispairs request/response rows.
  The case wipes its run dir at start (run dirs are disposable per AGENTS.md).
- The child's spawn cwd must exist (spawn ENOENTs otherwise).
- Responses are captured as raw SSE text; usage lives in `data:` frames.

## Files

- case: `cases/fabric-inject-update.case.mjs` (self-executing; run with
  `CC_MARKET_SHARED` to target a specific engine)
- fix: `cc-market/fabric/engine/spawn-child.mjs` (+ test update)
- capture: `.lab/fabric-inject-update/<a..f>/http.jsonl` (disposable)
