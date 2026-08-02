---
name: fabric-fanout-async
description: ai-post 08-02 — fabric fan_out/call long-running; harness must not treat fabric wait as stall; async backgrounding >120s; fabric plugin invisible to proxy layer
created: 2026-08-03
tags: [driver, struggle, fabric, MCP, async, deepseek]
---

# Fabric fan_out/call vs. the harness (analyzed 2026-08-02 ai-post)

Session `3189e129` used fabric heavily: 2× `fan_out` (deepseek, 4+3 tasks) + subagent
`call` (codex/deepseek, mode:agent). **Both `fan_out` exceeded the 120 s MCP window →**
synchronous tool_result only said "moved to background as task X"; the real JSON arrived
later as an async `<task-notification>` user-turn. All 7 tasks succeeded.

Full detail: `reports/fabric-fanout-async.md` (fabric/harness) + `reports/session-review-ai-post-20260802.md`
(full dual-session history).

## Harness implications → ✅ IMPLEMENTED 2026-08-03
1. **`fabric-wait` detector** — `driver/struggle.mjs` `fabricToolWaits()`: fabric MCP tool >120s
   backgrounded (`moved to the background as task X`) → kind `fabric-wait`, closed by its
   `<task-notification>`; orphaned → open episode. Excluded from struggles by default
   (`includeWaits` keeps them); `summarize()` reports `waitsOnFabric`.
2. **Async >120 s** — `driver/driver.mjs` `backgroundTaskPending()` + `waitIdle()`: a
   backgrounded fabric task is treated as **not idle** until its completion surfaces (avoids
   the send-behind-long-call race in proxy-profile-pitfalls #1). Tested.
3. **Evidence-layer-1 blind spot** (still open) — fabric `call`/`fan_out` are a plugin-MCP path
   to the cc-market fabric engine, NOT the child→observe-proxy HTTP MITM. Visible only in
   session jsonl (layer 2); `request.body.model` / `usage` for fabric work never reaches tap.
   Proxy must sit between fabric engine and its upstream to capture.
4. **Provider ad hoc** — subagents used codex + deepseek; main used deepseek only. post-review
   default provider (Opus+DeepSeek+Codex) ≠ user preference (deepseek-only); user corrected
   both sessions.
5. **Latency is normal** — fan_out wall-time ≈ slowest task; backgrounding is the normal path
   on slow providers, not a failure.

## Note
sharp-review subagents also hit `<tool_use_error>File has not been read yet` (Write before
Read) — known edit-thrash signature, matches 12 episodes.
