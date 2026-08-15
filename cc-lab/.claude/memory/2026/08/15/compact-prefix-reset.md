---
name: compact-prefix-reset
description: /compact does NOT zero cache_read on vanilla Sonnet — cache_read is pinned to system+tools (~65k), messages re-sent as uncached input; the [project] 600-800k cache_read is a DeepSeek accounting artifact (cache-reads whole warm context at ~1/50-1/120 input price), not extra tokens; 30-compact [subsystem] session: real context loss but convergent refactor not rework; PTY pitfall: send('/compact') merges into residual input
created: 2026-08-15
tags: [cache, compact, tokens, deepseek, sonnet, PTY, pitfalls, [project]]
---

# /compact prefix reset + 30-compact [subsystem] audit (2026-08-15)

## Experiment: cases/compact-prefix-reset.case.mjs (vanilla Sonnet, tap)

- cache_read is PINNED to system+tools (~65k) and does NOT drop to zero after `/compact`.
- The growing message history is sent as UNCACHED input (small input_tokens), NOT cache_read.
- Compaction resets the message prefix (msgs 7→5, summary injected as input ~2k) but cache_read stays ~60-73k.
- Verdict: "compact → from zero" is false for cache_read; only the message prefix resets.

## Reconcile with [project] DeepSeek 600-800k cache_read

- That is a **DeepSeek-backend accounting artifact**: it cache-reads the whole warm context (~1/50-1/120 of its input price), NOT extra tokens and NOT vanilla Anthropic behavior.
- Same conversation = same raw tokens on both; DeepSeek bills the history CHEAPER (cache_read) than Anthropic (which re-sends messages as full-price input).

## reports/compact-context-loss.md (30 compacts, session)

- Context loss is REAL: re-reads the worked source file ([src].py) at every window start.
- But it is NOT destructive rework — the heavy edit volume (463 edits in one day) was a CONVERGENT hard refactor (split >800-line [src].py into 5 modules).

## PTY harness pitfall

- `send('/compact')` merges the command into residual input text (tty showed "...single letter./compact"), treating it as a normal user message.
- Fix: **Ctrl+U (clear line) first**, then type '/compact' and submit with a separate Enter.
- Verify compaction via persisted-jsonl marker polling ("being continued"/"Compacted"), NOT UI silence.

## Committed

- `1b6f91e` (3 files: 2 reports + 1 case). Reports systematically scrubbed of PII: real username → `<user>`, real session IDs → `<session>`/`<tap-session>`.
