# compact-vs-fork — does compact on main affect a running fork?

**Answer: No.** The fork receives a full inline snapshot of the parent context at spawn
time. It does NOT re-read the parent JSONL on subsequent API calls. Compact on main
operates on main's in-memory context only and cannot affect a running fork.

Build: cc **2.1.209**, model Haiku, `CLAUDE_CODE_FORK_SUBAGENT=1`.
Case: `cases/compact-vs-fork.case.mjs`.

## Evidence

Tap session `b8273dad` captured 10 `/v1/messages` calls — 6 main turns, 3 fork turns
(identified by `cc_is_subagent=true` billing header), 1 auxiliary.

### 1. Parent context is fully inlined — not a live reference

The fork's first API call carries **5 messages**:

| # | Role | Content |
|---|------|---------|
| 0 | user | `<system-reminder>` — agent types, skills, git status... |
| 1 | assistant | `PARENT-TOKEN-ALPHA-ONE` |
| 2 | user | `Reply with exactly: PARENT-TOKEN-BETA-TWO` |
| 3 | assistant | `PARENT-TOKEN-BETA-TWO` |
| 4 | user | `<fork-boilerplate>` + directive |

Messages 0–3 are the **full parent conversation**, inlined verbatim. The word
`fork-context-ref` (which appears in the persisted JSONL as a bookkeeping marker) does
**not** appear anywhere in the API request body. The "reference" is resolved at spawn
time into a plain copy.

### 2. Parent context prefix is byte-identical across all fork turns

The fork made 3 API calls (directive processing + counting loop output + title-gen).
Across all 3 turns, the parent-derived message prefix (messages[0..3]) is **18,035
chars, byte-identical**:

| Fork turn | Messages | Input tok | Cache read | Parent prefix |
|-----------|----------|-----------|------------|---------------|
| 0 (spawn) | 5 | 10 | 47,304 | 18,035 chars |
| 1 (count) | 7 | 156 | 47,648 | 18,035 chars — **same** |
| 2 (aux)   | 7 | 8   | 48,067 | 18,035 chars — **same** |

Turn 1 grows by 2 messages (fork's own assistant response + next user prompt), but the
prefix is unchanged.

### 3. System prompt is byte-identical across fork turns

All 3 fork turns share the same 16,763-char system prompt (3 blocks, with
`cc_is_subagent=true` billing header). No dynamic elements differ between turns.

### 4. Cache sharing confirms structural identity

The fork's `cache_read` (47,304) matches the parent's last `cache_read` (47,304) —
both processes hit the same server-side cache entries for the identical system prompt
and tools schema. This is further confirmation that the fork uses a byte-identical copy,
not a live reference that could drift.

## Why compact can't affect a fork

1. **Fork context is a one-time copy** — resolved at spawn, inlined into the fork's
   first API request. No re-read of the parent JSONL on later turns.
2. **Fork has its own JSONL file** — `<sessionId>/subagents/agent-*.jsonl`. It grows
   independently; parent compact doesn't touch it.
3. **Compact is in-memory** — it summarizes main's context for the next main API call.
   It does not rewrite the persisted JSONL files (they are append-only).
4. **Separate processes** — the fork is a child process with its own context window.
   Even if compact did rewrite files (it doesn't), the fork wouldn't see the change
   mid-flight.

## One caveat: compact could affect a FUTURE fork

If you compact the main session and THEN spawn a new fork, the fork would inherit the
compacted (summarized) context. This is expected — the fork always gets a snapshot of
whatever the parent context is at spawn time. The "reference" in `fork-context-ref`
means "the parent's history at the time of forking," not "keep watching the parent."
