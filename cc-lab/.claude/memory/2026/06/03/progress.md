---
name: cc-lab-progress
description: cc-lab PLAN progress (M1 & M2 done, M3 & M4 pending) + key harness facts
metadata:
  type: project
---

# cc-lab progress

Tracks execution of `PLAN.md`. Most durable facts now live in `AGENT.md` — this file
records **where the plan stands** and the load-bearing findings a future session needs.

## PLAN status

- **M1 driver + evidence layer — DONE.** `driver/driver.mjs` (PTY wrapper:
  `send`/`key`/`waitOutput`/`waitIdle`/`ready`/`close`; isolated `CLAUDE_CONFIG_DIR`,
  credential bootstrap, ANSI strip, tap-session-id capture, defaults child to Haiku).
  `driver/tap.mjs` reads the trace DB. `cases/smoke.case.mjs` passes.
- **M2 thinking-cache — DONE.** `cases/thinking-cache.case.mjs` +
  `reports/thinking-cache.md`.
- **M3 behavior cases — DONE.** `cases/btw-isolation.case.mjs` + `reports/btw-isolation.md`,
  `cases/output-style-layer.case.mjs` + `reports/output-style-layer.md`,
  `cases/env-var-matrix.case.mjs` + `reports/env-var-matrix.md`.
- **M4 prompt-anatomy report — DONE.** `reports/prompt-anatomy.md` +
  `reports/system-prompt-anatomy.md` + `cases/system-prompt-diff.case.mjs`.

## Load-bearing facts (see AGENT.md for detail)

- **Traces are NOT in `--tap-output-dir`** (that flag is a legacy one-shot import dir).
  They live in the shared sqlite `~/.local/share/claude-tap/traces.sqlite3`, keyed by the
  `Trace session: <uuid>` line printed at startup (captured as `session.tapSessionId`).
- **Records are compact blob-ref encoded:** real payload nested under `.record`; large
  fields (tools, big messages) offloaded to `record_blobs`. Always read via
  `driver/tap.mjs` (`loadRecords` rehydrates); never raw SQL.
- **Main-turn isolation heuristic:** `Array.isArray(system) && tools.length>0 &&
  response.body.usage` present — filters out title-gen / classifier / `max_tokens:1`
  quota (404) calls.
- **Thinking control is the `/effort` slider** (←/→ + Enter + a Yes/No confirm), NOT
  Shift+Tab (which cycles permission modes).
- **Cost rule:** cases default to Haiku, Sonnet at most, never Opus for convenience.

## Headline finding (M2)

Switching reasoning **effort** mid-session **fully invalidates the prompt cache**:
next turn `cache_read → 0` and re-creates the entire ~49k-token prefix, despite a
byte-identical system prompt / tools / cache breakpoints. Effort is a **server-side
cache-key dimension**; the body's `thinking` field doesn't even change. Detail +
evidence table: `reports/thinking-cache.md`.

## Commits

`0b22543` (M1) · `281aa52` (M2) · `53b5ec2` (Haiku cost control).
