# output-style-layer (PLAN M3.2) — where does a session directive layer in, and does cache survive?

**Two findings:**

1. **Output styles are removed in this build (cc 2.1.199).** There is no `/output-style`,
   `/style`, or `/output` command — the slash menu returns *"No commands match"*. The
   PLAN's literal target no longer exists.
2. **A mid-session directive (`/goal`) enters at the _message/history_ layer, not the
   system prompt — and the prompt cache survives it.** This is the clean opposite of the
   `/effort` switch (which is a server-side cache-key dimension and busts the whole cache,
   see `reports/thinking-cache.md`).

## Method

`cases/output-style-layer.case.mjs`: turn 1 (no directive, marker MANGOONE) → set
`/goal Always include the token GOALPINE …` → turn 2 (marker PAPAYATWO). Compare the
`system` array (per-block hash) and messages across the two main turns; read cache usage.
Run `.lab/2026-07-03T13-49-33-output-style-layer/`, tap session `47319760…`.

## Evidence

| turn | role | system hash (all 3 blocks) | GOALPINE in system | GOALPINE in messages | cache_read | cache_create |
|------|------|----------------------------|--------------------|----------------------|-----------|--------------|
| 3  | T1 (no goal)  | `dcff55fbce` | — | — | 37 534 | 7 107 |
| 5  | T1 cont.      | `dcff55fbce` | — | — | 44 641 | 65 |
| 53 | T2 (goal set) | `dcff55fbce` | — | **✓** | 45 010 | **15** |

- **System prompt unchanged.** Every turn has the identical 3-block system array
  (`dcff55fbce`; per-block hashes match). `/goal` does not add or edit a system block.
- **The directive lands in message history.** In the turn-2 request, GOALPINE appears in
  a dedicated user message:
  `<command-message>goal</command-message><command-args>Always include the token
  GOALPINE in every reply.</command-args>` — i.e. a slash-command turn recorded like any
  other user input, followed by the assistant's acknowledgement. It is **not** a
  system-reminder and **not** in the system prompt.
- **Cache survives.** `cache_read` stays ~45k across the switch and `cache_create` for
  turn 2 is 15 tokens — the cached system+history prefix is reused; only the new
  directive turn is added incrementally.

## Interpretation — the layering

| layer | example | how a change enters | cache effect |
|-------|---------|---------------------|--------------|
| **cache-key dimension** | `/effort` level | not in the body at all (server-side key) | **full bust** — cache_read → 0 |
| **system prompt** (3 blocks) | CLI version, Claude Code identity, agent instructions | stable per session; `cache_control` ephemeral 1h on blocks 1–2 | reused |
| **message/history** | `/goal`, normal turns, `/btw` | appended as a user/assistant turn | incremental; prefix reused |

Session directives that Claude Code exposes as slash commands (`/goal`) flow through the
**message layer**, so they are cheap (cache-preserving). Only a cache-key dimension like
effort forces a full re-creation. If output styles still existed, this case would show
which layer they mutated; their removal is itself the answer for this build.

## Notes

- Substituting `/goal` for the removed `/output-style` keeps M3.2's methodological intent
  (which layer changes + cache impact) answerable on this build.
- A future build that re-introduces output styles (or a custom style file) should be
  re-tested here: a style that edits a *system* block would, unlike `/goal`, be expected
  to bust the system-prefix cache from its breakpoint onward.
