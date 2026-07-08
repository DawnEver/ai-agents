# thinking-cache — does toggling thinking/effort mid-session break prompt-cache hits?

**Answer: Yes on first visit — but it's cache *partitioning*, not a global reset.**
Switching effort mid-session makes the next turn read from that effort's OWN cache
namespace: a **first-ever** visit to an effort level cold-misses and re-creates the whole
prefix (the run below), but switching **back** to a previously-used level **recovers** its
cache within the TTL. See the **Follow-up** section for the round-trip evidence and the
refined mechanism; the original single-switch run (cold miss → zero cached tokens) is
below.

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
- Not tested in the original run: whether *raising* effort also busts the cache, and
  whether the pre-switch breakpoints survive a switch-back. Both are now answered in the
  follow-up below.

## Follow-up — effort partitions the cache; round-trips RECOVER (cc 2.1.204)

`cases/thinking-cache-recovery.case.mjs` runs a high→low→high→low round trip in one
session (default effort is **high** in this build) and reads `output_config.effort` —
in cc 2.1.204 the effort level is now visible **in the request body** at
`output_config.effort`, so the old "body byte-identical" no longer holds. The real main
turns are isolated from the client's `[SUGGESTION MODE …]` autocomplete calls (which
also carry system+tools+usage and otherwise pollute `mainTurns`).

Run: tap session `7ed02197-3cb7-4781-a306-e187e5ac0cb4`.

| turn | msg | effort | switch | **cache_read** | **cache_create** |
|------|-----|--------|--------|---------------|-----------------|
| T1 | apple  | high | (default)     | 50 626 | 9 730 |
| T2 | banana | low  | high→low      | 50 626 | 10 896 |
| T3 | cherry | high | low→high (**raise**) | **60 356** | **1 355** |
| T4 | date   | low  | high→low      | 61 522 | **376** |

The smoking gun: **T3's `cache_read` is ~9 730 higher than T2's — exactly the block T1
created at high effort.** T2 @ low could not reuse T1's high block (so it created its own
10 896-token low block); T3 switching back to high **recovered T1's block verbatim**,
collapsing create to 1 355. T4 back to low likewise recovered T2's low block (create 376).
If an effort switch globally reset the cache, T3/T4 would each re-create the whole
prefix (~10k+), not 1–2k.

**Refined conclusion.** An effort switch does **not** globally orphan the cache. Effort
is a cache-key *dimension*, so each level keeps an **independent** cache namespace:
switching to effort X **hits** X's cache if it still exists within the (1h) TTL, else
**cold-misses** and rebuilds. So:

- **(Q1) Raising also "busts" — but only as a cold miss.** low→high (T3) *recovered*
  rather than rebuilt, because high was already cached. Direction is irrelevant; what
  matters is whether the target effort's cache is warm.
- **(Q2) Yes, pre-switch breakpoints survive a switch-away-and-back.** high→low→high
  recovered the high block (T1→T3); the low block likewise survived high→low→…→low.

This reframes the original run's `cache_read → 0`: that was a **first-ever visit to that
effort level** (cold miss), not a global "reset." Caveat: the ~50.6k cross-session
tools+identity prefix stayed a hit through every switch here because dozens of same-day
runs had already warmed **both** effort levels — the original run cold-missed it precisely
because it was the first low-effort visit of the day. The clean, same-session recovery
signal is the session-specific block (T1's 9 730 → recovered at T3), which is unaffected
by that cross-session confound.

## Notes / pitfalls (follow-up)

- **The cache-invalidation confirm dialog is conditional.** In cc 2.1.204 switching to a
  *lower* level (→ low) pops the "Change effort level? … Switching to low means the full
  history gets re-read … 1. Yes, switch to low" dialog; a small change / raise applies
  directly with just a `⎿ Set effort level to <X>` result line and no dialog. A driver
  must handle **both** paths (poll: result line → done, dialog → accept).
- **`/effort` picker-open is racy.** The submit sometimes doesn't render the slider, and
  then a stray `←` is eaten by the main UI ("← for agents") and navigates to the agents
  dashboard. Gate arrows on a picker-unique token ("Esc to cancel") and retry, never on
  `waitIdle`.
- **Word-concatenation bites the result line.** stripAnsi turns "Set effort level to low"
  into `Seteffortleveltolow` (spaces are cursor-forward escapes) — match with `\s*`
  between words. The dialog *title* happens to keep real spaces; the result line does not.
