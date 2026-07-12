# fabric-vs-fork — Fabric (new resultMode) vs Built-in Subagent

**Question.** How does the new fabric — with `resultMode` summarization and non-codex write
sessions — compare to the built-in `/fork` subagent on token consumption, parent context
pollution, and capability boundaries?

**Method.** Offline cost model based on fork-context-flow trace data (cc 2.1.205, Haiku,
`subagent_tokens=46500` per stop) and fabric code analysis. Live case: `cases/fabric-vs-fork.case.mjs`.

**Build.** cc `HEAD`, fabric `38c5dba`, Fable 5 parent, DeepSeek v4-pro child.

## Code Changes Analyzed

The fabric plugin (cc-market/fabric) now has two new features that directly impact the
comparison:

### 1. `resultMode` — Parent Context Pollution Control

`mcp-server.mjs:419-430` — Three modes on `call` and `session_send`:

| Mode | Behavior | Parent pollution |
|------|----------|-----------------|
| `"summary"` (default) | Outputs >2000 chars → cheap follow-up call condenses to ~150 tok | ~300 tok |
| `"full"` | Complete output, unchanged | Full child output (2000+ tok) |
| `"truncate"` | Char-based truncation at `maxResultChars` | ~500 tok |

Three summary paths: API provider HTTP (DeepSeek haiku-tier), codex app-server, DeepSeek
backstop for native Claude. Falls back to truncate at 4000 chars on failure.

### 2. Write Sessions for Non-Codex Providers

`engine/session.mjs:16-42` — `openWriteSession()` spawns `claude -p --allowedTools` per
turn, accumulating conversation history in the prompt. Each turn repays for prior context
but gets full file-editing and command-execution capability.

## Token Cost Comparison

### Single Task: "Review this code for bugs" (~2000 tok output)

| Scenario | Child cost | Summary call | Parent pollution | Parent next-turn | **Total** | Write? |
|---|---|---|---|---|---|---|
| **Fork (Haiku)** | $0.102 | — | 120 tok ($0.001) | $0.001 | **$0.104** | no |
| **Fabric summary (DeepSeek)** | $0.002 | $0.001 | 300 tok ($0.003) | $0.003 | **$0.006** | no |
| **Fabric full (DeepSeek)** | $0.002 | — | 2000 tok ($0.020) | $0.020 | **$0.022** | no |
| **Fabric truncate (DeepSeek)** | $0.002 | — | 500 tok ($0.005) | $0.005 | **$0.007** | no |
| **Fabric write 3-turn (DeepSeek)** | $0.008 | $0.003 | 900 tok ($0.009) | $0.009 | **$0.020** | **YES** |

### 10× Parallel Fan-out

| Approach | Child cost | Parent pollution | Parent next-turn | **Total** |
|---|---|---|---|---|
| **10× Fork (Haiku)** | $1.023 | 1.2k tok ($0.012) | $0.012 | **$1.035** |
| **10× Fabric summary (DeepSeek)** | $0.020 | 3.0k tok ($0.030) | $0.030 | **$0.060** |
| **10× Fabric full (DeepSeek)** | $0.020 | 20.0k tok ($0.200) | $0.200 | **$0.220** |

## Capability Boundaries

| Capability | Fork (built-in) | Fabric `call` | Fabric write session |
|---|---|---|---|
| Edit files | **no** (fork write-isolation) | no (read-only) | **yes** (`--allowedTools`) |
| Run commands | no (unless BTW) | no | **yes** (`--allowedTools`) |
| Context retention | Inherits parent by ref | None (stateless) | History in prompt (repays) |
| Parent visibility | Result-callback only | Summary by default | Summary per turn |
| Multi-turn | Yes (resume via agents view) | No | Yes (`session_send` × N) |
| Provider flexibility | Parent's account only | **Any configured provider** | **Any configured provider** |
| Fan-out mechanism | Workflow (parallel forks) | N concurrent `call()` | N concurrent sessions |

## Decision Matrix

| Use case | Best tool | Why |
|---|---|---|
| Cheap one-shot investigation | **fabric `call`:summary** | 17× cheaper than fork; summary keeps parent clean |
| Full-result code review | **fabric `call`:full** | 5× cheaper child cost; fork has less parent pollution |
| Multi-turn editing (write files) | **fabric write session** | Fork **cannot write** due to isolation |
| Long multi-turn investigation | **fork** | Context by ref → no history repayment |
| 10× parallel research fan-out | **fabric `call`:summary** | 17× cheaper; parent sees 10 short summaries |
| No API provider configured | **fork** | Fabric needs an API provider for best economics |

## Key Findings

1. **Fabric:summary is 17× cheaper than fork for single tasks** — DeepSeek child ($0.002)
   vs Haiku fork (~$0.102). The summary call adds ~$0.001 but keeps parent context clean.

2. **Parent context pollution is the dominant hidden cost.** Fabric:full dumps 2000 tok
   into parent ($0.02/round on Fable 5). Fabric:summary reduces this to 300 tok ($0.003).
   Fork's notification is even smaller (120 tok) but the child cost dominates.

3. **10× fan-out amplifies the gap.** Fork: $1.04 total. Fabric:summary: $0.06 total.
   The fork's Haiku subagent_tokens scale linearly; DeepSeek stays flat.

4. **Write capability is fabric's exclusive territory.** Fork write-isolation is a Claude
   Code platform constraint — no workaround. Fabric write sessions get `--allowedTools
   Bash,Read,Write,Edit,Glob,Grep` with `--permission-mode bypassPermissions`.

5. **Fork's context-by-reference is uniquely efficient for long conversations.** Fabric
   write sessions repay history each turn (turn 3 pays for turns 1+2). Fork inherits once
   at spawn and runs forward-isolated.

6. **Summary fallback is robust.** Three paths (API HTTP → codex app-server → DeepSeek
   backstop) with truncation as final fallback. A summary failure costs ~$0.001 and falls
   back to 4000-char truncation — not a data-loss scenario.

## Files

- `cases/fabric-vs-fork.case.mjs` — Live comparison case (auto-registers fabric MCP)
- `.scratch/fabric-vs-fork-cost-model.mjs` — Offline cost model script
- `reports/fabric-vs-fork.md` — This report
- cc-market commit `38c5dba` — The fabric changes being evaluated
