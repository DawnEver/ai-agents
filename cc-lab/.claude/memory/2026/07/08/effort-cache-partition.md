---
name: effort-cache-partition
description: reasoning effort partitions the prompt cache — each level has its own namespace; round-trips recover within TTL
created: 2026-07-08
tags: [thinking-cache, effort, prompt-cache, cc-2.1.204, driver]
---

# effort partitions the prompt cache — round-trips recover

Refines `reports/thinking-cache.md`. New case `cases/thinking-cache-recovery.case.mjs`
(Sonnet) drives a real CC session through a **high→low→high→low** `/effort` round trip and
reads the tap trace DB. Committed `33675ba`.

## Finding

Reasoning **effort is a cache-key dimension**: each effort level keeps an **independent
cache namespace**. Switching to a level **HITS** its cache if warm within the (~1h) TTL,
else **cold-misses** and rebuilds. It is NOT a global reset.

Round-trip proof (tap session `7ed02197…`, real turns only):

| turn | effort | switch | cache_read | cache_create |
|---|---|---|---|---|
| T1 apple | high | default | 50626 | 9730 |
| T2 banana | low | high→low | 50626 | 10896 |
| T3 cherry | high | low→high (raise) | **60356** | **1355** |
| T4 date | low | high→low | 61522 | **376** |

Smoking gun: T3's read is ~9730 higher than T2's = exactly T1's high-block create. T2@low
couldn't reuse T1's high block (built its own low block, create 10896); T3 back to high
**recovered T1's block verbatim** (create collapses to 1355); T4 back to low recovered T2's
low block (create 376). Full-reset would re-create ~10k+ each time, not 1–2k.

- **Q1 raising also busts?** No — direction is irrelevant; only cache *warmth* matters. A
  raise recovers if that level is warm, else cold-misses like any first visit.
- **Q2 do pre-switch breakpoints survive switch-away-and-back?** Yes (within TTL).
- Original report's `read→0` was a **cold first-visit miss**, not a global reset. Caveat:
  the ~50.6k cross-session tools+identity prefix stayed a hit through every switch here only
  because dozens of same-day runs had pre-warmed **both** levels; the clean same-session
  signal is the session-specific block (T1's 9730 → recovered at T3).
- **effort level is now visible in the request body** at `output_config.effort` (cc 2.1.204);
  the old "body byte-identical across effort" no longer holds.

## Driver gotchas (cc 2.1.204)

- **Cache-invalidation confirm dialog is CONDITIONAL.** Only a *downgrade* (→ low) pops
  "Change effort level? … 1. Yes, switch to low"; a raise / small change applies directly
  with just `⎿ Set effort level to <X>`. A driver must handle **both** paths (poll: result
  line → done, dialog → accept).
- **`/effort` picker-open is RACY.** The submit sometimes doesn't render the slider; a stray
  `←` then navigates the main UI to the **agents view**. Gate arrows on a picker-unique token
  (**"Esc to cancel"**) + retry — never `waitIdle`.
- **stripAnsi word-concatenates the result line** → `Seteffortleveltolow`; match with `\s*`
  between words. The dialog *title* keeps real spaces; the result line does not.
- **`mainTurns()` catches the client's `[SUGGESTION MODE …]` autocomplete calls** (they carry
  system+tools+usage too) — filter them out to get the real turns.
- **claude-tap was missing on this machine** — install via `uv tool install claude-tap`
  (0.1.126, lands in `~/.local/bin`; the driver resolves it there).
- Fixed a pre-existing SyntaxError in `cases/thinking-cache.case.mjs` (duplicate
  `const runDir`, referenced undefined `stamp`).

## Convention

`.scratch/` is the gitignored unified path for throwaway analysis scripts (ana/peek/probe,
tty dumps); only reusable experiments earn a `cases/<name>.case.mjs`. Documented in AGENT.md.
