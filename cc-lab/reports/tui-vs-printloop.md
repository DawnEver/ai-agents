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

**Parity controls (post-review):** both claude modes pass the same `--allowedTools
Bash,Read,Write,Edit,Glob,Grep` so the tool schema is identical. `--permission-mode` is
deliberately NOT set in either mode — `bypassPermissions` pops a startup dialog whose
default selection is "No, exit" (kills the child under PTY automation), and
`acceptEdits` re-renders the status bar so the driver's ready-marker never appears;
omitting it from both keeps the permission instructions identical. This deviates from
fabric's exact spawn flags (which use `--permission-mode bypassPermissions`) — the
measurement isolates process architecture, and permission mode is a documented
divergence.

## Measured results

Cold-cache runs with ≥5-min gaps (the cache is only semi-cold — see finding 4; the
1-hour ephemeral tier keeps the shared prefix warm). Claude numbers from the claude-tap
DB; codex from session `token_count` / `tokens used`.

### A. claude TUI (one process, 3 turns) — run `.lab/2026-08-09T20-19-14-...` (fixed code: `--allowedTools` parity, suggestion calls accounted)

| turn | input | output | cache_read | cache_create |
|------|-------|--------|-----------|--------------|
| T1 | 10 | 243 | 39,791 | 9,159 |
| T2 | 10 | 280 | 49,200 | 23 |
| T3 | 10 | 255 | 49,510 | 16 |
| **Σ** | **30** | **778** | **138,501** | **9,198** |

Plus **1 suggestion-mode call**: 350 fresh + 49,526 read + 262 create + 4 out (real
billed traffic, reported separately — excluded from the main-turn table).

### B. claude -p loop (3 fresh processes, history via stdin) — run `.lab/2026-08-09T20-29-40-...` (fixed code, cold)

| turn | input | output | cache_read | cache_create |
|------|-------|--------|-----------|--------------|
| T1 | 10 | 235 | 33,696 | 8,596 |
| T2 | 10 | 273 | 33,696 | 8,797 |
| T3 | 10 | 340 | 37,286 | 5,304 |
| **Σ** | **30** | **848** | **104,678** | **22,697** |

Context retention verified: T2's request carries T1+T2 history; replies answer the
right turn (T2: "A query like `SELECT * FROM Users WHERE email = …`", T3 merges T1+T2).
T3's read jump (33,696 → 37,286) and create drop (8,797 → 5,304): its system prompt is
byte-identical to T2's (verified 0-diff), so the server-side cache hit across processes.

### C. codex TUI (one process, 3 turns — cumulative token_count per turn)

| turn | input (cum) | cached (cum) | fresh ≈ (delta) |
|------|-------------|--------------|-----------------|
| T1 | 15,557 | 5,888 | 9,669 |
| T2 | 31,202 | 20,992 | 541 |
| T3 | 46,919 | 36,096 | 613 |
| **Σ** | **46,919** | **36,096** | **~10,823** |

### D. codex exec loop (3 fresh processes — session token_count per turn)

| turn | input | cached | fresh ≈ (input−cached) | output | `tokens used` (stderr) |
|------|-------|--------|------------------------|--------|------------------------|
| T1 | 16,154 | 6,912 | 9,242 | 63 | 9,305 |
| T2 | 16,237 | 6,912 | 9,325 | 54 | 9,379 |
| T3 | 16,303 | 11,008 | 5,295 | 59 | 5,354 |
| **Σ** | **48,694** | **24,832** | **23,862** | **176** | **24,038** |

`tokens used N` (stderr) ≈ input − cached = the fresh (non-cached) tokens per process.
Note T3's cached jump (6.9k → 11.0k): codex exec sessions DO share prompt-cache across
processes — the re-sent history prefix from T1/T2's sessions is cache-readable (the
earlier "no cross-process cache" claim was unsupported and is corrected here).

## Billed cost (claude modes; haiku 4.5: $1 fresh / $1.25 creation / $0.10 cache-read / $5 output per MTok)

Cold-cache runs (cold-A `.lab/2026-08-09T20-19-14-...`, cold-B `.lab/2026-08-09T20-29-40-...`):

| mode | fresh | creation | read | output | est. cost |
|------|-------|----------|------|--------|-----------|
| TUI (main turns) | 30 | 9,198 | 138,501 | 778 | **$0.029** |
| TUI (+1 suggestion call) | 380 | 9,460 | 188,027 | 782 | **$0.035** |
| -p loop | 30 | 22,697 | 104,678 | 848 | **$0.043** |

The -p loop bills **≈1.5× the TUI (main turns)** in this semi-warm environment: it
re-pays ~8.6k of system-prompt-tail creation on every fresh process (see finding 8 for
why), while the TUI creates it once. On a fully warm cache the -p loop measured 0
creation + 42.2k read/turn when run right after the TUI. **fabric 0.1.15 removes this
gap architecturally** (write sessions are now a persistent stream-json child, same
process-per-conversation structure as the TUI — verified, see finding 3). Codex modes
are token-only (pricing not public); fresh-token totals: TUI ~10.8k vs exec loop ~28.1k.

## Key findings

1. **TUI pays creation once, then reads.** T1 creates the ~9k session-specific prefix
   (+ reads the 39.8k shared prefix); T2/T3 are ~99.9% cache reads (49.1k/49.3k, ~20
   tokens created). 3 turns ≈ 9.1k creation + 138.2k read + 30 fresh.

2. **The -p loop re-pays ~8.6k of system-prompt tail per process but shares its cache
   cross-process.** Each fresh process reads 33.7–37.3k (the shared 33.7k prefix — see
   finding 8) and creates ~5–9k. T3 reads content that T2's process cached (creation
   drops 8.8k → 5.3k): prompt-cache entries are server-side content-addressed, not
   process-scoped. The earlier "37k cache-miss every -p turn" model is wrong.

3. **`claude -p` truncates a multi-line argv prompt at the first newline** (measured on
   claude 2.1.226; not verified against other builds). Measured: `User: Q1\n\nAssistant:
   A1\n\nUser: Q2` sends ONLY `User: Q1` to the API. Passing the prompt via **stdin**
   preserves the full history (verified: T2's request carries T1+T2). **Fixed in fabric
   0.1.15, verified 2026-08-09**: `spawn-child.mjs` forces the stream-json stdin path
   whenever the prompt contains a newline (its comment cites this exact 2.1.226
   measurement), and the stateless `openWriteSession` argv-replay path is retired
   entirely — write sessions are now the same long-lived stream-json child as read
   sessions ("O(n²) tokens and hits the ~32k Windows command-line ceiling around turn
   5-10", SR-024/049). Live 2-turn test on 0.1.15 passed (turn 2 recalled turn 1's
   content). **Consequence for cost parity (the goal of this experiment): fabric's
   write-session cost structure is now identical to the TUI's** — one process, prefix
   created once. The remaining ~1.5× gap in the table above is specific to the
   per-turn-fresh-process `claude -p` pattern (finding 8).

4. **The 1-hour ephemeral cache tier keeps this environment semi-warm.** usage shows
   `ephemeral_1h_input_tokens` (not the 5m tier) for the session prefix; even "cold"
   runs (≥15-min gaps) read ~33.7k of the 42.2k prefix. A fully cold first-run would
   create ~42–49k on T1 (structure visible in the creation column).

5. **codex TUI harness (~15.6k input/turn) vs codex exec (~16.2k input/turn, ~9.3k
   fresh)** — the TUI ships extra system context (skills, multi-agent instructions) but
   caches in-session (15.1k cached/turn after T1, ~0.5k fresh); exec re-pays ~9.2k
   fresh/turn but also benefits from cross-process cache on the re-sent history (T3:
   11.0k cached). Fresh-token totals: TUI ~10.8k vs exec ~23.9k; total-input totals:
   46.9k vs 48.7k.

6. **claude harness ≈ 42–49k tokens vs codex ≈ 9.3–16.2k** — a 3–5× system-prompt ratio.

7. **Suggestion calls are real billed traffic in the TUI and are now accounted
   separately** (`suggestionCost` bucket): cc 2.1.226 fires "[SUGGESTION MODE]" calls
   after replies (~350 fresh + ~49k cached read each, detected via the last user
   message — the marker lives there, not in the system blocks). They are excluded from
   the main-turn cost but reported so the TUI column's total is complete.

8. **Why the -p loop re-pays ~8.6k per process (and the lever to close it).** The
   claude system prompt has three parts: (a) a ~33.7k shared prefix (global + project
   CLAUDE.md, rules, template head) that is byte-stable across ALL claude sessions on
   this machine — cache-read 33,696 on every -p process regardless of warmth; (b) a
   per-process tail that is NOT byte-stable between cold runs — T1 vs T2 of cold-B
   diverge at char 14,598 (a `gitStatus` block shifts vs. a template paragraph), and
   every byte after the first divergence misses the cache; (c) the growing message
   history. Within one run the tail IS stable (T2 vs T3: 0 diffs) and the cache hits
   across processes immediately (T3: +3,590 read / −3,493 create). So a `claude -p`
   loop reaches TUI cost exactly when its system tail is byte-identical to the previous
   process's — the remaining divergence is claude CLI-side dynamic injection (git
   status, session markers), not fabric-side. fabric 0.1.15 sidesteps it for write
   sessions by keeping one process (finding 3). The 1h ephemeral tier
   (`ephemeral_1h_input_tokens`, confirmed in raw usage) is what keeps part (a) warm
   across the ≥10-min gaps here.

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
