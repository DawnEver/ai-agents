---
name: tui-vs-printloop
description: live token measurement TUI vs -p loop (claude + codex); claude -p argv prompt truncation breaks fabric write-session replay; cc 2.1.226 TUI queue/suggestion quirks; driver tap strips provider env for vanilla routing
created: 2026-08-09
tags: [tokens, cache, TUI, print-loop, fabric, codex, driver, pitfalls]
---

# TUI vs -p loop token measurement + harness fixes (2026-08-09)

Live comparison of the same 3-turn task: claude interactive TUI vs fabric-style
`claude -p` loop (fresh process per turn, history replayed), plus the same pair for
codex. Full data: `reports/tui-vs-printloop.md`. Case: `cases/tui-vs-printloop.case.mjs`
(supports `--phases=AB` for cache-cold runs).

## Findings (measured 2026-08-09, claude 2.1.226 / codex 0.147)
1. **TUI (3 turns)**: 30 fresh + 9,059 creation + 138,206 read ≈ **$0.030** (haiku 4.5).
   T1 creates the ~9k session-specific prefix; T2/T3 are ~99.9% cache reads (49k/turn).
2. **-p loop (3 fresh processes, stdin history)**: 30 fresh + 22,520 creation +
   104,670 read ≈ **$0.043** (~1.4× TUI). Re-pays the session prefix per process;
   cross-process cache sharing works (T3 reads T2's cached content). **The "37k
   cache-miss per fresh -p process" assumption in fabric-vs-fork/long-running-token-cost
   is wrong — on a warm cache the -p loop measured 0 creation + 42.2k read/turn.**
3. **`claude -p` truncates a multi-line argv prompt at the first newline** — only the
   first line reaches the API. Prompt via **stdin** preserves the full history
   (verified: T2's request carried T1+T2). Implication: fabric `engine/session.mjs`
   `openWriteSession` passes the joined history as one argv arg → **its replay is lost
   on this build** (every session_send re-asks only the first line).
4. **The 1-hour ephemeral cache tier** (`ephemeral_1h_input_tokens`) keeps the shared
   prefix warm across runs; "cold" runs (15-min gaps) still read ~33.7k. Fully-cold
   structure is visible in the creation column.
5. **codex TUI ~15.6k input/turn vs codex exec ~9.3k/turn** (TUI ships extra system
   context). codex TUI caches in-session (15.1k/turn after T1, ~0.6k fresh); codex exec
   has no cross-process cache (~9.3k fresh/turn; 28.1k total vs TUI 46.9k). claude
   harness ~42–49k vs codex ~9–16k (3–5×).

## Harness fixes (all driver/case changes)
- **driver.mjs tap mode now also strips `ANTHROPIC_BASE_URL`/`ANTHROPIC_API_KEY`/
  `ANTHROPIC_AUTH_TOKEN`**: otherwise tap auto-detects the parent's provider gateway
  (deepseek) as upstream and forwards the claude.ai OAuth Bearer there → 401 "api key
  invalid". Vanilla routing = credential-free child + copied OAuth → api.anthropic.com.
- **cc 2.1.226 TUI multi-turn**: post-reply messages queue and stall (reported
  queue-stall bug; a single Enter queues). Working pattern: text + Enter + (1.5s) +
  Enter. Exclude "[SUGGESTION MODE]" calls from turn counts (system prompt contains
  SUGGESTION; they echo long text when the queue is polluted). Sync on the tap DB
  (dispatched turns), never TTY idle.
- **codex 0.147 TUI**: `-c tui.starter_suggestions=false`; turns after the first need
  Enter twice. Sync on `token_count` event_msg in the session jsonl (flushes live per
  turn). Session files: filter by `session_meta.cwd` (concurrent sessions share the dir).
- **codex exec**: spawn with `stdio:['ignore',...]` (waits forever on an open stdin);
  "tokens used" goes to **stderr**.
- **Prompt-cache warmth is a persistent confound on this machine** — the user's own
  claude sessions keep the shared prefix cached; "cold" runs still read ~40k.
