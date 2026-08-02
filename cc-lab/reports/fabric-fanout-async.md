# fabric-fanout-async — Fabric MCP tooling vs. the cc-lab harness (2026-08-02 ai-post)

**Session.** ai-post `3189e129-52bc-4556-8ee6-c45fcc8391ed` (agent-24x7-dev / tone-chord-lab
v1→v2), real user session — evidence layer 2 only (persisted jsonl; no tap/proxy on this run).

**Question.** Today's ai-post work leaned hard on fabric. What does that usage expose about
the harness's ability to observe a child that uses the fabric MCP plugin?

## Fabric usage observed (today)

| Site | Tool | Provider(s) | Mode | Tasks | Timeout / outcome |
|---|---|---|---|---|---|
| Main session | `fan_out` | deepseek | synthesize:true | 4 (`A-xhs`, …) | **>120 s → backgrounded** (`kieetrpq0`), 4/4 ok |
| Main session | `fan_out` | deepseek | synthesize:true | 3 (`A-twitter-rerun`, …) | **>120 s → backgrounded** (`k1xgkcr9i`), 3/3 ok |
| sharp-review subagent (`acae…`) | `call` | codex ×2, deepseek ×1 | agent (docs review) | — | synchronous |
| docs-review subagent (`a683…`) | `call` | codex ×1, deepseek ×1 | agent (docs review) | — | synchronous |
| main + subagents | `list_providers` | — | — | — | ok |

Both `fan_out` calls exceeded the **120 s MCP-tool window**. The synchronous `tool_result`
carried only *"still running after 120s … moved to the background as task X"*; the real JSON
result arrived later as an **async `<task-notification>` user-turn** (`{"ok":true,"count":4…}`).
All 7 fan-out tasks eventually succeeded.

## Harness gaps this exposes

1. **`long-stall` false positives on fabric.** The struggle detector flagged 5 `long-stall`
   episodes (85/76/72/71/48 assistant entries). A child mid-`fan_out` / `call mode:agent` is
   TTY-quiet for a legitimate reason — fabric routes to an external engine (deepseek/codex),
   so the child's turn spans real wall-time with no local tool churn. `detectStruggles` /
   `waitIdle` cannot currently tell "stalled" from "waiting on fabric." Fix: recognize an
   in-flight fabric `tool_use` in the trace and (a) suppress/annotate the `long-stall` or
   (b) emit a distinct `waits-on-fabric` episode kind (mirror `waits-on-subagents`, which is
   counted but was 0).

2. **Async backgrounding of MCP tools > 120 s.** `fan_out` is the one cc-market MCP tool that
   routinely exceeds the 120 s window and silently becomes a background task. Harness sync
   primitives were designed around *synchronous* tool results:
   - `waitIdle()` fires on TTY-idle; the child is explicitly told *"you can keep working,"* so
     if it chooses to wait for the fan-out, TTY goes quiet while the task is still running.
     A send queued at that instant lands behind a still-running fabric call → lost or reordered
     turn (the exact failure mode already documented for `waitIdle` racing slow upstreams in
     `proxy-profile-pitfalls` #1, but now from the *child's own* tool).
   - Fix: `waitIdle` should treat a pending `<task-notification>`-carrying fabric tool as
     "not idle" (poll the trace for the `background as task …` marker; wait for the matching
     notification row before declaring idle).

3. **Fabric plugin calls are invisible to evidence layer 1.** The `proxy` observe profile
   MITMs the child's HTTP upstream through observe-proxy — but `fabric/call` and `fan_out`
   are a *separate* plugin-MCP path that talks straight to the cc-market fabric engine
   (which owns the deepseek/codex upstream). Consequences:
   - fabric invocations surface **only** in evidence layer 2 (main + subagent jsonl), never
     in `<runDir>/http.jsonl`.
   - `request.body.model` / `response.body.usage` for fabric work are absent from tap — fabric
     owns model routing (`deepseek-v4-flash/pro`), so token & cost attribution for the fabric
     portion is a blind spot. `cc-market-token-audit.md` noted the same (fabric MCP tools not
     captured in that run).
   - Fix: document this capture boundary in the observe-profile docs; if fabric capture is
     wanted, the observe-proxy must sit *between* the fabric engine and its upstream, or the
     fabric engine needs its own tap/proxy hook — not the child→upstream MITM.

4. **Provider choice in fan-out is ad hoc.** Subagents used both `codex` and `deepseek`
   (`mode:agent`); the main session used only `deepseek`. Codex `call` results were not
   observed returning clean text in this trace (deepseek ones did). The harness should not
   assume a single provider for fabric work when asserting on results.

5. **Aggregate latency is real, not pathological.** 4-task and 3-task `fan_out` *both* blew
   the 120 s budget against deepseek. For cost-control guidance this is expected, not a bug:
   `fan_out` wall-time ≈ slowest task, so backgrounding is the *normal* path on slow providers.
   A case that asserts on `fan_out` must wait for the notification, not the tool_result.

## Not fabric, but surrounding
sharp-review subagents hit `<tool_use_error>File has not been read yet` (Write to a memory
file they hadn't Read) — matches the 12 `edit-thrash` episodes. This is the workflow the
harness drives; worth keeping in the edit-thrash detector as a known signature.

## Recommendation (harness) — ✅ IMPLEMENTED 2026-08-03
- `driver/struggle.mjs`: added `fabricToolWaits()` → kind `fabric-wait` (fabric MCP tool >120s
  backgrounded, closed by its `<task-notification>`; orphaned → open episode). Excluded from
  struggles by default (`opts.includeWaits`), counted as `waitsOnFabric` in `summarize()`.
- `driver/driver.mjs`: added `backgroundTaskPending()`; `waitIdle()` now treats a backgrounded
  fabric task as **not idle** until its completion surfaces.
- `scripts/analyze-session.mjs`: header prints `waits-on-fabric`.
- `test/struggle.test.mjs` (new, `npm test`, 5 cases green).
- Verified on real data: tone-chord `waits-on-fabric: 2`, agent-24x7 `waits-on-fabric: 2`.

Still open (capture layer): fabric plugin `call`/`fan_out` are a plugin-MCP path to the cc-market
fabric engine, NOT the child→observe-proxy HTTP MITM — visible only in evidence layer 2. To capture
them at layer 1, the observe-proxy must sit *between* the fabric engine and its upstream, or the
fabric engine needs its own tap/proxy hook. Observe-profile docs should state this boundary.
