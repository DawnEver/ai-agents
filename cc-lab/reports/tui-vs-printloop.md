# TUI vs -p Loop — Same 3-Turn Task, Token Consumption (Claude & Codex)

**Date:** 2026-08-09 | **Build:** claude 2.1.226, codex-cli 0.147.0, claude-tap 0.1.126
**Prior work:** `reports/fabric-vs-fork.md`, `reports/long-running-token-cost.md` (offline cost models — this report measures live)

## Question

The same 3-turn task executed four ways; measured token consumption per mode:

| # | Mode | Process architecture | Measurement source |
|---|------|---------------------|--------------------|
| A | **claude interactive TUI** | one persistent PTY session | claude-tap DB (`usage` per main turn) |
| B | **claude -p loop** (fabric `openWriteSession` pattern) | fresh `claude -p` process per turn, history replayed in the prompt | claude-tap DB (one trace session per process) |
| C | **codex interactive TUI** | one persistent PTY session | `~/.codex/sessions/*.jsonl` `token_count` (cumulative) |
| D | **codex exec loop** | fresh `codex exec` process per turn, history re-sent | codex `tokens used N` (stderr) |

Task (identical text in all modes; T2/T3 reference prior answers):
- T1: "In 2-3 sentences, explain what a database index is."
- T2: "From your previous answer, give one concrete example query that the index would speed up, and why."
- T3: "Merge your first and second answers into a single final sentence."

Claude modes pinned to `claude-haiku-4-5-20251001`; codex used its configured default (gpt-5.6-sol). Both claude modes run **vanilla** against api.anthropic.com with the copied claude.ai OAuth (the driver's tap mode strips the parent's provider base-url/API-key env — see "Measurement setup" below).

## Measured results

Cold-cache runs with ≥5-min gaps (the cache is only semi-cold — see finding 4; the
1-hour ephemeral tier keeps the shared prefix warm). Claude numbers from the claude-tap
DB; codex from session `token_count` / `tokens used`.

### A. claude TUI (one process, 3 turns) — run `.lab/2026-08-09T19-11-44-...`

| turn | input | output | cache_read | cache_create |
|------|-------|--------|-----------|--------------|
| T1 | 10 | 265 | 39,791 | 9,020 |
| T2 | 10 | 219 | 49,083 | 23 |
| T3 | 10 | 420 | 49,332 | 16 |
| **Σ** | **30** | **904** | **138,206** | **9,059** |

### B. claude -p loop (3 fresh processes, history via stdin) — run `.lab/2026-08-09T19-25-09-...`

| turn | input | output | cache_read | cache_create |
|------|-------|--------|-----------|--------------|
| T1 | 10 | 219 | 33,696 | 8,551 |
| T2 | 10 | 298 | 33,696 | 8,724 |
| T3 | 10 | 258 | 37,278 | 5,245 |
| **Σ** | **30** | **775** | **104,670** | **22,520** |

Context retention verified: T2's request carries T1+T2 history; replies answer the
right turn (T2: "A query like `SELECT * FROM Users WHERE email = …`", T3 merges T1+T2).

### C. codex TUI (one process, 3 turns — cumulative token_count per turn)

| turn | input (cum) | cached (cum) | fresh ≈ (delta) |
|------|-------------|--------------|-----------------|
| T1 | 15,557 | 5,888 | 9,669 |
| T2 | 31,202 | 20,992 | 541 |
| T3 | 46,919 | 36,096 | 613 |
| **Σ** | **46,919** | **36,096** | **~10,823** |

### D. codex exec loop (3 fresh processes)

| turn | tokens |
|------|--------|
| T1 | 9,304 |
| T2 | 9,357 |
| T3 | 9,426 |
| **Σ** | **28,087** |

## Billed cost (claude modes; haiku 4.5: $1 fresh / $1.25 creation / $0.10 cache-read / $5 output per MTok)

| mode | fresh | creation | read | output | est. cost |
|------|-------|----------|------|--------|-----------|
| TUI | 30 | 9,059 | 138,206 | 904 | **$0.030** |
| -p loop | 30 | 22,520 | 104,670 | 775 | **$0.043** |

The -p loop bills **≈1.4× the TUI** in this (semi-warm) environment: it re-pays the
~8.5k session-specific prefix creation on every fresh process, while the TUI creates it
once. On a fully warm cache the -p loop can be cheaper (measured 0 creation + 42.2k
read/turn when run right after the TUI — see finding 3). Codex modes are token-only
(pricing not public); fresh-token totals: TUI ~10.8k vs exec loop ~28.1k.

## Key findings

1. **TUI pays creation once, then reads.** T1 creates the ~9k session-specific prefix
   (+ reads the 39.8k shared prefix); T2/T3 are ~99.9% cache reads (49.1k/49.3k, ~20
   tokens created). 3 turns ≈ 9.1k creation + 138.2k read + 30 fresh.

2. **The -p loop re-pays the session prefix per process but shares its own cache
   cross-process.** Each fresh process creates ~5–9k (its session-specific prefix + new
   history suffix) and reads 33.7–37.3k. T3 reads content that T2's process cached
   (creation drops 8.7k → 5.2k): prompt-cache entries are server-side content-addressed,
   not process-scoped. The earlier "37k cache-miss every -p turn" model is wrong.

3. **`claude -p` truncates a multi-line argv prompt at the first newline.** Measured:
   `User: Q1\n\nAssistant: A1\n\nUser: Q2` sends ONLY `User: Q1` to the API. Passing the
   prompt via **stdin** preserves the full history (verified: T2's request carries T1+T2).
   **Implication: fabric's `openWriteSession` (`engine/session.mjs`) passes the joined
   history as one argv argument — on this build the replay is lost; every `session_send`
   re-asks only the first line.** Its "history repayment" cost model needs revisiting.

4. **The 1-hour ephemeral cache tier keeps this environment semi-warm.** usage shows
   `ephemeral_1h_input_tokens` (not the 5m tier) for the session prefix; even "cold"
   runs (≥15-min gaps) read ~33.7k of the 42.2k prefix. A fully cold first-run would
   create ~42–49k on T1 (structure visible in the creation column).

5. **codex TUI harness (~15.6k input/turn) > codex exec harness (~9.3k/turn)** — the TUI
   ships extra system context (skills, multi-agent instructions); exec is leaner. Both
   cache in-session (codex TUI: 15.1k cached/turn after T1, ~0.6k fresh); codex exec has
   no cross-process cache (~9.3k fresh every turn). Fresh-token totals favor the TUI
   (~10.8k vs ~28.1k), total-token totals favor exec (28.1k vs 46.9k).

6. **claude harness ≈ 42–49k tokens vs codex ≈ 9.3–15.6k** — a 3–5× system-prompt ratio.

## Measurement setup & pitfalls (for reuse)

- **Auth/routing:** the parent env carries a provider base URL + API key (deepseek gateway).
  In tap mode the driver now strips `ANTHROPIC_BASE_URL` / `ANTHROPIC_API_KEY` /
  `ANTHROPIC_AUTH_TOKEN` too — otherwise tap auto-detects the gateway upstream and forwards
  the claude.ai OAuth Bearer there (401 "api key invalid"). With the vars stripped, both
  claude modes route vanilla to api.anthropic.com via the copied OAuth creds.
- **cc 2.1.226 TUI multi-turn:** a message sent after a reply lands in the CLI-side message
  queue and stalls (never dispatches; the reported queue-stall bug). A single Enter queues;
  sending text + Enter + (1.5 s) + Enter dispatches reliably. The post-reply "[SUGGESTION
  MODE]" call must be excluded from turn counting (system prompt contains SUGGESTION; it
  responds with long echo text when the queue is polluted). TTY idle is not a reliable sync —
  poll the tap DB for dispatched turns.
- **codex 0.147 TUI:** `-c tui.starter_suggestions=false` kills the startup suggestion menu;
  turns after the first need Enter twice (first arms, second submits — single Enter leaves
  the text stuck in the input box). Turn completion sync: `token_count` event_msg entries
  flush live per turn in the session jsonl. Session files are keyed by `session_meta.cwd` —
  other concurrent codex sessions (user's own, fabric app-server) write into the same dir;
  filter by cwd, never by recency.
- **codex exec:** reads stdin and waits forever on an open pipe — spawn with `stdio:
  ['ignore', ...]`. The `tokens used N` summary goes to **stderr**.
- **Prompt-cache warmth is a confound:** claude 2.1.226 marks the session prefix with the
  **1-hour** ephemeral cache tier (`ephemeral_1h_input_tokens`), so back-to-back phases and
  even ≥15-min-gap "cold" runs share the shared prefix; only the session-specific creation
  (~9k) is reliably re-paid. Codex's cache is independent (own account/backend) but also
  TTL'd (its `cached_input_tokens` grows in-session).

## Run artifacts

- Case: `cases/tui-vs-printloop.case.mjs` (self-executing; `--phases=AB` for cold runs)
- Runs: `.lab/2026-08-09T18-59-04-tui-vs-printloop-37152/` (all 4 phases) + cold A/B runs
- Traces: shared claude-tap sqlite DB (tap-session UUIDs in the run dirs / usage.json)
