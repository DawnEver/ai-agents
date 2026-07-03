# prompt-anatomy (PLAN M4) — mapping the Claude Code request prefix

Pure analysis over accumulated traces (no new code). Maps the request's cacheable prefix
into its stable vs per-session-variable segments and locates the cache breakpoints, using
the tap DB via `driver/tap.mjs`. Build cc 2.1.199, model Haiku (structure is model-independent).

## The request prefix, in order

An `/v1/messages` main turn is built from three top-level parts, cached in this order:
**tools → system[] → messages[]**. Sizes from a representative fresh-session main turn:

| part | segment | size | `cache_control` | stable across sessions? |
|------|---------|------|-----------------|--------------------------|
| `tools` | 35 tools | ~134 KB JSON | none of its own | **yes** (hash `79184dce` everywhere) |
| `system[0]` | billing header `cc_version=…; cc_entrypoint=cli;` | 70 ch | **none** | yes (per build) |
| `system[1]` | identity `You are Claude Code…` | 57 ch | **ephemeral 1h** ← breakpoint A | yes (`2719b7a4`) |
| `system[2]` | the agent instructions | 15.8 KB | **ephemeral 1h** ← breakpoint B | **no — varies every session** |
| `messages[0]` | dynamic context (system-reminders) + user text | ~10 KB | **ephemeral 1h** on last block | no (per turn) |

## Two cache breakpoints, two segments

The `cache_control` markers on `system[1]` and `system[2]` split the prefix into two
independently-cached segments — and the split is deliberate:

- **Segment A = tools + system[0] + system[1]** (ends at breakpoint A). This is the huge,
  fully-stable part (~134 KB of tools + the identity line). It is **cache-read across
  sessions**: a brand-new session's very first main turn reports **`cache_read = 37 534`**
  — i.e. ~37.5k tokens were reused from a prior session's cache, before this session sent
  anything. The tools schema dominates this segment.
- **Segment B = system[2]** (ends at breakpoint B). ~15.8 KB / ~4k tokens. This is
  **re-created every session**: the same first turn shows **`cache_create ≈ 7 124`**
  (segment B + the first message's dynamic context).

So cross-session caching already works for the expensive part (tools). The per-session
cost is segment B + the message-layer context.

## Why segment B misses cross-session cache — and it's avoidable

`system[2]` is 122 lines; diffing it across sessions shows it is **byte-identical except
for exactly two lines**:

- line 72 — `Primary working directory: …/.lab/<timestamp>-<name>/…`
- line 86 — the scratchpad temp path, which embeds a **per-session UUID**

Those two lines sit in the *middle* of the block, before its single breakpoint, so any
change to them invalidates the **entire ~4k-token block2 segment** for cross-session
reuse. The UUID in the scratchpad path guarantees a fresh value every session, so block2
can *never* be shared across sessions as currently built.

**"Useless/wasteful prompt" candidate (cache efficiency):** the ~4k-token re-creation of
block2 every session buys only two lines of path info. If the cwd and scratchpad lines
were moved to the **message layer** (where Claude Code already puts the rest of the
per-session env context) or placed **after** breakpoint B, the whole 15.8 KB instruction
block would become cross-session cacheable like the tools. This is a placement issue, not
a content issue — the instructions themselves are stable.

## The message layer (per-turn variable context)

`messages[0]` of a turn carries the genuinely dynamic context as `<system-reminder>`
blocks, with `cache_control` on the **last** block so the prefix up to it is cached:

- block 0 (~2.4 KB): available agent types for the `Agent` tool.
- block 1 (~7.9 KB): the big session context — `claudeMd`, memory index, skills list,
  session guidance, current date, opened-file hint.
- block 2 (tiny): the actual user message.

This is where session/turn variance *should* live (and mostly does) — it is expected to
re-create each turn and does not pretend to be a stable prefix.

## Takeaways

1. The expensive prefix (35-tool schema, ~37.5k tokens) is **already shared across
   sessions** via breakpoint A — good design.
2. The 15.8 KB instruction block is stable *content* but is **cache-orphaned per session
   by two embedded path lines** (cwd + scratchpad UUID). Relocating those two lines would
   make it cross-session cacheable, saving ~4k tokens of `cache_create` per new session.
3. Combined with the other findings: `/effort` busts **both** segments (server-side
   cache-key), `/goal` and normal turns append only in the **message layer** (cheap),
   and the two `DISABLE_*` env vars studied are no-ops here. See the other reports.
