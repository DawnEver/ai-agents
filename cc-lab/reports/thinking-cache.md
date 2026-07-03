# thinking-cache — does toggling thinking/effort mid-session break prompt-cache hits?

**Answer: Yes, completely.** Lowering the reasoning **effort** level mid-session
invalidates the *entire* prompt cache. The next turn reads **zero** cached tokens and
re-creates the whole ~49k-token prefix — even though the request's system prompt, tools,
and cache-breakpoint markers are byte-for-byte identical to the previous turn.

## Method

`cases/thinking-cache.case.mjs`: launch real Claude Code under claude-tap →
turn 1 ("reply apple") at the default effort **high** → open `/effort`, move the slider
two steps left, confirm → turn 2 ("reply banana") at effort **low** → close.
Assertions are read from the tap trace DB (`driver/tap.mjs`), not the screen.

Run: `.lab/2026-07-03T13-24-24-thinking-cache/`, tap session
`331b52b4-6e5d-44b4-930d-10beac0cb140`.

## Evidence (main-thread `/v1/messages` turns)

| turn | msg | effort | `thinking` (body) | input | **cache_read** | **cache_create** | out |
|------|-----|--------|-------------------|-------|---------------|-----------------|-----|
| 3    | apple  | high | `{type:adaptive}` | 757 | **43 452** | 4 543 | 4 |
| 22   | banana | low  | `{type:adaptive}` | 2   | **0**      | **48 935** | 4 |

- `system` array hash identical across both turns (`6a33bf0cc667`); `tools` identical
  (35 tools); both carry the same cache breakpoints (`ephemeral, ttl:1h` on system
  blocks 1 & 2) and the same `anthropic-beta` set including `effort-2025-11-24` and
  `extended-cache-ttl-2025-04-11`.
- Nothing in the cacheable request content changed — yet turn 2's `cache_read` is 0 and
  it re-creates the full 48 935-token prefix.

**Conclusion:** the reasoning-effort level is a *server-side cache-key dimension*.
Because the cache key includes effort, switching effort orphans every existing
breakpoint at once; the identical prompt text cannot be reused. Note the body's
`thinking` field stayed `adaptive` in both turns — the invalidation is driven by the
effort switch, not by any visible change to the `thinking` request parameter.

## Corroborating UI signal (input channel, not the assertion)

Confirming the `/effort` change pops a dialog that states the mechanism outright:

> Change effort level? … This conversation is cached for the current effort level.
> Switching to low means the full history gets re-read on your next message.

Claude Code itself treats an effort switch as a full cache reset. The trace confirms it.

## Notes / pitfalls discovered

- **Shift+Tab does not toggle thinking** in this build (cc 2.1.199) — it cycles
  *permission* modes (accept-edits / plan). Thinking/effort is the `/effort` command.
- `/effort` is a **horizontal slider** (low·medium·high·xhigh·max·ultracode·
  xhigh+workflows), driven by ←/→ and Enter, followed by a Yes/No cache-invalidation
  confirmation. A vertical-menu assumption (Down arrow) is a no-op.
- Not tested here: whether *raising* effort or a same-level re-confirm also busts the
  cache, and whether the pre-switch `1h` breakpoints survive to a later switch-back.
  A follow-up case could switch low→high→low and check for any cache_read recovery.
