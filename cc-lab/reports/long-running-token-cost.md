# Long-Running Token Cost — Fan-Out, Fork, Fabric, Team Mode

**Date:** 2026-07-12 | **Build:** cc HEAD | **Prior work:** `reports/fabric-vs-fork.md`

## Question

How do the four agent-delegation mechanisms compare on token consumption for **long-running
multi-turn tasks**? The existing `fabric-vs-fork` report covered single-turn costs
exhaustively; this report models growth with turn count (N) and parallel fan-out (K).

## Mechanisms Compared

| # | Mechanism | How | Multi-turn? | Context model |
|---|---|-----------|------------|---------------|
| 1 | **Fork** (`/fork`) | CC built-in subagent | Yes (agents view) | Context-by-reference (free after spawn) |
| 2 | **Fabric `fan_out`** | MCP tool: K parallel single-turn calls + optional synthesis | No (per task) | Stateless — each task is one `call()` |
| 3 | **Fabric `team_*`** (team mode) | MCP tools: `team_spawn` → N× `team_send` → `team_synthesize` | Yes (per worker) | Persistent session per worker |
| 4 | **Workflow `agent()`** | CC built-in: orchestrates parallel subagents | Yes (per agent) | Context-by-reference (same as fork) |

Fabric team mode has two sub-flavours:

| Flavour | Backend | Write files? | Per-turn harness |
|---------|---------|-------------|-----------------|
| Team read-only | Persistent stream-json `claude` child | No | 0 (cached after T1) |
| Team write (non-codex) | Fresh `claude -p` per turn | **Yes** | ~37k tok (cache miss every turn) |
| Team write (codex) | App-server thread | **Yes** | 0 (native context retention) |

## CC Built-in "Team Mode" vs Fabric Team Mode

Claude Code has no standalone "team" feature. Its built-in fan-out mechanism is the
**Agent/Workflow** system (mechanism #4 above):

- **Agent tool** (`Agent()`) — spawns a single subagent. Each subagent is identical to
  a `/fork`: context-by-reference, Haiku, write-isolation, result-callback notification.
- **Workflow tool** (`Workflow()`) — orchestrates multiple Agent calls in parallel or
  pipeline patterns. Adds a thin orchestration layer (~500-800 tok overhead per fan-out
  round for the Workflow script and coordination).

This is fundamentally different from fabric's **team mode** (`team_spawn`/`team_send`/
`team_synthesize`):

| Dimension | CC Agent/Workflow | Fabric team mode |
|-----------|-------------------|-----------------|
| Spawn mechanism | Agent tool (CC built-in) | `team_spawn` MCP tool |
| Worker backend | Haiku fork subagent | Persistent session (any provider) |
| Context model | Context-by-reference (free) | Persistent session (cache works) |
| Write files? | No (write-isolation) | Yes (with `write:true`) |
| Provider | Haiku only (Anthropic) | Any configured provider |
| Cross-worker synthesis | Manual (parent must merge) | `team_synthesize` auto-synthesis |
| Orchestration | Workflow script (JS) | Manual (parent calls team_send per worker) |
| Per-worker cost scaling | O(N) linear | O(N) linear (read-only) / O(N²) (write, non-codex) |

**The core tradeoff:** CC's Agent/Workflow is simpler (no MCP dependency, no provider
config) but locked to Haiku and can't write files. Fabric team mode is more flexible
(any provider, can write) but requires MCP setup and provider configuration.

For long-running tasks, both have O(N) scaling in their read-only forms — the key
difference is provider pricing (Haiku $1/$5 vs DeepSeek $0.435/$0.87 per MTok).

## Architecture: Why Scaling Differs

### Fork — O(N) flat

```
Parent ──/fork──→ [Fork session: inherits parent context by reference]
                    T1: full harness (50k) + user → cache created
                    T2: only new messages (3k input) → cache HIT
                    T3: only new messages (3k input) → cache HIT
                    ...
Each stop → <task-notification> (~120 tok) posted to parent
```

The fork's persistent session means the CC prompt cache lives across turns. Each
additional turn costs only the incremental conversation delta (~3k input + ~5k output).
Parent pollution is minimal: 120 tok per notification.

### Fabric write session (non-codex) — O(N²)

```
Parent ──session_send──→ [Fresh claude -p process]
                           T1: 37k harness + 0.5k user → 37.5k input
Parent ──session_send──→ [Fresh claude -p process]
                           T2: 37k harness + 0.5k user + 5.5k history → 43k input
Parent ──session_send──→ [Fresh claude -p process]
                           T3: 37k harness + 0.5k user + 11k history → 48.5k input
```

Each `session_send` spawns a **new** `claude -p` process → zero cache sharing → the full
37k CC harness is re-charged every turn. Additionally, the entire conversation history is
replayed in the prompt. Input at turn T:
```
input(T) = 37,000 + 500 + (T-1) × 5,500
total(N) = N × 37,500 + N(N-1)/2 × 5,500
```

This is O(N²). A planned fix (persistent stream-json with `--allowedTools`) would drop
the 37k harness term, converting to O(N²) with a much smaller constant — same as the
codex path.

### Fabric team (read-only) — O(N) flat

```
Parent ──team_spawn──→ [Persistent stream-json claude child per worker]
Parent ──team_send───→ T1: full harness (50k) → cache created
Parent ──team_send───→ T2: only new messages → cache HIT
Parent ──team_send───→ T3: only new messages → cache HIT
Parent ──team_synthesize──→ reads all worker histories, generates summary
```

Same architecture as fork (persistent process, cache alive across turns), but with
provider flexibility (any configured provider, not just Haiku). The `team_synthesize`
call adds a small fixed cost per fan-out round.

### Fabric fan_out — O(K) single-turn

```
Parent ──fan_out([task1, task2, ..., taskK])──→ K parallel handleCall() invocations
                                                   each: stateless, single-turn
                                                   optional: synthesis call
Result: compact JSON with summaries (capped 400 chars each)
```

Pure parallelism of single-turn calls. No multi-turn capability per task — each task is
one `handleCall()` invocation. Best for research sweeps where each question is
self-contained.

### Workflow agent() — O(K × N) flat

```
Parent ──Workflow──→ [Agent 1: context-by-reference, N turns]
                     [Agent 2: context-by-reference, N turns]
                     ...
                     [Agent K: context-by-reference, N turns]
```

Same context model as fork (context-by-reference, cache works). Each agent is an
independent subagent. The Workflow tool orchestrates them in pipeline/parallel patterns.

## Single-Agent Long-Running Cost (N turns)

Task: multi-turn investigation, ~5k tok output per turn.

| N | Fork (Haiku) | Team read-only (DS) | WS non-codex (DS) | WS codex (DS) |
|---:|---:|---:|---:|---:|
| 1 | $0.076 | $0.031 | $0.025 | $0.009 |
| 3 | $0.135 | $0.052 | $0.081 | $0.033 |
| 5 | $0.193 | $0.074 | $0.148 | $0.067 |
| 10 | $0.339 | $0.127 | $0.355 | $0.194 |
| 20 | $0.631 | $0.234 | $0.950 | $0.628 |

**Key observations:**

1. **At N=1**, write session (codex) wins at $0.009 — the cheapest single-turn option
   because it skips the full CC harness that fork/team pay on first turn.

2. **At N=3**, team read-only ($0.052) beats fork ($0.135) — DeepSeek pricing dominates.
   Write session non-codex ($0.081) is still reasonable.

3. **At N=5**, the write session non-codex ($0.148) starts to diverge from the O(N) pack
   due to history repayment growth.

4. **At N=10**, write session non-codex ($0.355) crosses above fork ($0.339). Team
   read-only ($0.127) is 2.7× cheaper than fork.

5. **At N=20**, write session non-codex ($0.950) is the most expensive. Team read-only
   ($0.234) is 2.7× cheaper than fork ($0.631).

**The crossover where fork becomes cheaper than write session (non-codex) is at N≈10.**
At that point, the history repayment cost in write sessions equals the higher per-token
Haiku pricing of fork.

## Fan-Out Cost: K Parallel Agents, M Turns Each

| Config | Fork (Haiku) | fan_out (DS) | Team write non-codex | Team write codex | Team read-only | Workflow agent() |
|---|---:|---:|---:|---:|---:|---:|
| 3×1 | $0.229 | **$0.012** | $0.081 | $0.033 | $0.100 | $0.239 |
| 3×5 | $0.579 | N/A | $0.450 | $0.208 | **$0.228** | $0.611 |
| 10×1 | $0.762 | **$0.026** | $0.254 | $0.093 | $0.318 | $0.785 |
| 10×3 | $1.346 | N/A | $0.821 | $0.338 | **$0.531** | $1.405 |

**Key observations:**

1. **For M=1 (single-turn fan-out): fan_out dominates.** At 10×1, fan_out is $0.026 vs
   fork at $0.762 — a 29× gap. The synthesis call adds ~$0.002.

2. **For M>1 (multi-turn fan-out): team read-only wins.** At 10×3, team read-only
   ($0.531) is 2.5× cheaper than fork ($1.346) and 2.6× cheaper than Workflow ($1.405).

3. **fan_out is single-turn only.** It cannot do M>1. For multi-turn parallel work, the
   choice is between team mode and Workflow.

4. **Team write (codex) is viable for short multi-turn.** At 3×5, codex write ($0.208) is
   competitive with team read-only ($0.228). The codex backend avoids the 37k harness
   penalty that non-codex write sessions pay.

5. **Workflow agent() ≈ parallel forks.** Similar scaling, slightly higher cost due to
   orchestration overhead from the Workflow tool's own token consumption.

## Parent Context Pollution

A hidden cost that grows with fan-out width:

| Mechanism | Pollution per child turn | At K=10, M=3 |
|-----------|------------------------|--------------|
| Fork | ~120 tok (notification) | 3.6k tok |
| fan_out | ~500 tok (compact JSON) | 0.5k tok (single result) |
| Team (per worker) | ~500 tok (result per team_send) | 15k tok |
| Workflow agent() | ~300 tok (return value) | 9k tok |

Fork has the smallest per-turn pollution (120 tok notification), but it adds up with
K×M stops. fan_out has the smallest total pollution (single compact JSON result).
Team mode and Workflow have higher per-turn pollution because results flow through MCP
tool responses or agent return values.

## Decision Matrix

| Task | Best | Rationale |
|------|------|-----------|
| 1–20 parallel one-shot queries | **fan_out** | 29× cheaper than fork at K=10; auto-synthesis |
| Single multi-turn investigation (no write) | **Team read-only** or **Fork** | Team: cheaper provider. Fork: simpler UX (agents view) |
| Single multi-turn investigation (needs write) | **Team write (codex)** | Only option that can write; codex avoids 37k harness |
| Short editing task (1–3 turns) | **Team write (any)** | O(N²) penalty is small at low N; any provider works |
| Long editing task (4+ turns) | **Team write (codex)** | Non-codex O(N²) becomes prohibitive; codex stays flat |
| Parallel multi-turn (K×M, M>1) | **Team read-only** | Cheapest at scale (2.5× cheaper than Workflow) |
| Parallel multi-turn + write | **Team write (codex)** | Only option; codex keeps harness cost at 0 |
| No external API configured | **Fork** or **Workflow** | Fabric needs an API provider for best economics |

## Caveats

1. **Cost model, not live measurement.** These numbers come from an offline model
   calibrated against fork-context-flow trace data (Haiku `subagent_tokens=46500`, CC
   harness ~37k tok). A live case with `observe: 'proxy'` would capture actual DeepSeek
   token counts and should be run to validate.

2. **Team read-only assumes stream-json cache works.** The model assumes the persistent
   `claude --stream-json` child maintains prompt cache across `send()` calls. This
   matches fork behavior but hasn't been independently verified for fabric sessions.

3. **Summary/synthesis costs are estimates.** The model uses constants from the
   `fabric-vs-fork` report for summary call costs. Actual costs depend on task verbosity.

4. **Codex pricing not modeled separately.** Codex write sessions use DeepSeek pricing
   in this model. Actual codex app-server pricing may differ.

5. **Workflow orchestration overhead is an estimate.** The Workflow tool itself consumes
   tokens to orchestrate agents. The model adds ~800 tok/agent for this but hasn't been
   measured directly.

## Files

- `reports/long-running-token-cost.md` — This report
- `.scratch/long-running-cost-model.mjs` — Offline cost model (run to reproduce tables)
- `reports/fabric-vs-fork.md` — Prior single-turn comparison
- `.scratch/fabric-vs-fork-cost-model.mjs` — Prior single-turn cost model
- `reports/fork-context-flow.md` — Fork notification model (subagent_tokens constant)
