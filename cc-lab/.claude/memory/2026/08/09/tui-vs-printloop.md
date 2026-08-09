---
name: tui-vs-printloop
description: live token measurement TUI vs -p loop (claude + codex); claude -p argv truncation fixed in fabric 0.1.15 (stdin + persistent child = TUI cost structure); -p per-process 8.6k creation traced to byte-unstable system tail; cc 2.1.226 TUI queue/suggestion quirks
created: 2026-08-09
tags: [tokens, cache, TUI, print-loop, fabric, codex, driver, pitfalls]
---

# TUI vs -p loop token measurement + harness fixes (2026-08-09)

Live comparison of the same 3-turn task: claude interactive TUI vs fabric-style
`claude -p` loop (fresh process per turn, history replayed), plus the same pair for
codex. Full data: `reports/tui-vs-printloop.md`. Case: `cases/tui-vs-printloop.case.mjs`
(supports `--phases=AB` for cache-cold runs).

## Findings (measured 2026-08-09, claude 2.1.226 / codex 0.147; cold-cache runs)
1. **TUI (3 turns, cold-A 20-19-14)**: 30 fresh + 9,198 creation + 138,501 read ≈
   **$0.029** (haiku 4.5; +1 suggestion call → ~$0.035). T1 creates the ~9k
   session-specific prefix; T2/T3 are ~99.9% cache reads (49k/turn).
2. **-p loop (3 fresh processes, stdin history, cold-B 20-29-40)**: 30 fresh + 22,697
   creation + 104,678 read ≈ **$0.043** (~1.5× TUI). Re-pays ~8.6k system-tail per
   process; cross-process cache sharing works (T3 reads T2's cached content). **The
   "37k cache-miss per fresh -p process" assumption in
   fabric-vs-fork/long-running-token-cost is wrong** — on a warm cache the -p loop
   measured 0 creation + 42.2k read/turn.
3. **`claude -p` truncates a multi-line argv prompt at the first newline** — only the
   first line reaches the API. Prompt via **stdin** preserves the full history.
   **FIXED in fabric 0.1.15** (verified 2026-08-09): `spawn-child.mjs` forces
   stream-json stdin on any newline in the prompt (comment cites our 2.1.226
   measurement); the stateless argv-replay `openWriteSession` is retired — write
   sessions are now the same long-lived stream-json child as read sessions → **cost
   structure identical to the TUI** (one process, prefix created once). Live 2-turn
   test passed.
4. **The 1-hour ephemeral cache tier** (`ephemeral_1h_input_tokens`) keeps the shared
   prefix warm across runs; "cold" runs (10-min gaps) still read ~33.7k.
5. **codex TUI ~15.6k input/turn vs codex exec ~9.3k/turn** (TUI ships extra system
   context). codex TUI caches in-session (15.1k/turn after T1, ~0.6k fresh); codex exec
   has no cross-process cache (~9.3k fresh/turn; 28.1k total vs TUI 46.9k). claude
   harness ~42–49k vs codex ~9–16k (3–5×).
6. **Why -p re-pays ~8.6k/process (mechanism)**: system prompt = (a) ~33.7k
   byte-stable shared prefix (CLAUDE.md/rules/template head — cached across ALL claude
   sessions on the machine, read 33,696 on every -p process) + (b) a per-process tail
   that is NOT byte-stable between cold runs (cold-B T1 vs T2 diverge at char 14,598 —
   a `gitStatus` block shifts vs a template paragraph; every byte after the first
   divergence misses) + (c) growing history. Within one run the tail IS stable (T2 vs
   T3: 0 diffs) and cross-process cache hits immediately (T3: +3,590 read / −3,493
   create). **A -p loop reaches TUI cost exactly when its system tail is byte-identical
   to the previous process's — remaining divergence is claude CLI-side dynamic
   injection, not fabric-side.**
7. **Static `--system-prompt` injection closes the stateless gap — VERIFIED (tap
   capture, vanilla api.anthropic.com, haiku 4.5)**: request structure =
   `system[billing][base][--system-prompt text]` + `user[CLAUDE.md/rules ~6k][prompt
   w/ cache_control]` + `tools ~36k`. First process create 6,379; same static prompt
   next process reads 25,752 / creates 0 (full cross-process hit); different prompt
   → 19,373+6,379. History grows in prompt (stdin) → after a warm first call each turn
   pays only appended history (+139/+254 on 3-turn loop). **3-turn static -p ≈ $0.005
   vs TUI $0.029 / default -p $0.043.** Must use `--system-prompt` (REPLACE), not
   `--append-system-prompt` (sits past the unstable tail). `--system-prompt` replaces
   the base template (behavioral text must be authored; tools in body.tools unaffected;
   CLAUDE.md/rules still inject). **Fabric: spawn-child.mjs concatenates systemPrompt
   into the prompt string — no cache benefit; must pass it via --system-prompt flag
   and keep history on stdin.**

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
