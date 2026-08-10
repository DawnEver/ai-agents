# effort-deepseek — do `/effort` levels actually change DeepSeek behavior?

**Question:** on the DeepSeek Anthropic-compatible endpoint, what *actually* differs across
`/effort` levels (high/xhigh/max/low/ultracode)? Prior research (the docs summary) said the
wire carries `output_config.effort` and effort is a cache-key dimension on Anthropic — but
DeepSeek has its own cache semantics (`cache_creation` always 0) and its own model family.
Measure, don't assume.

**Answer (short):** the level reaches the wire and is accepted; `ultracode` genuinely sends
`xhigh`; but DeepSeek's upstream **ignores effort for its context cache** (switching effort
never cold-misses — the opposite of Anthropic), and for a numeric trap probe the model's
output/thinking/latency barely move across levels. On this evidence, effort is close to a
**no-op upstream** for DeepSeek-v4-pro via the Anthropic-compatible endpoint — you pay
nothing extra for switching, but you also don't get deeper reasoning.

## Method

`cases/effort-deepseek.case.mjs`: one real interactive Claude Code session via
`observe:'proxy'` (provider deepseek, ccds env layout with the full capability set
`effort,xhigh_effort,max_effort,…` so the `/effort` slider exposes every level). Walked the
slider high (default) → xhigh → max → low → ultracode, one probe turn per level, all
measurements from the proxy capture `<runDir>/http.jsonl` (evidence layer 1). Probe: the
"snail in a well" numeric trap, one variant per level (different H/c/s) so later turns can't
repeat the previous answer. Expected day = `ceil((H−c)/(c−s)) + 1`.

Runs: `.lab/2026-08-10T19-10-29-effort-deepseek-74356` (full capture, all 5 levels landed),
re-run with the hardened case at `.lab/2026-08-10T19-15-15-effort-deepseek-65756` (clean
PASS). Both runs agree on every finding; `think_chars`/`dur_ms`/`output` vary run-to-run
non-monotonically (e.g. xhigh: 415 → 694) — noise, supporting the "no clear effort effect"
conclusion.

## Per-level table (real main turns = tool-bearing requests in order)

| turn | requested | **wire effort** | input | **cache_read** | cache_create | output | think_chars | dur_ms | answer |
|------|-----------|-----------------|-------|----------------|--------------|--------|-------------|--------|--------|
| 1 | high | `high` | 31 272 | **0** (cold) | 0 | 235 | 549 | 6 651 | ✓ 8 |
| 2 | xhigh | `xhigh` | 596 | **31 232** | 0 | 173 | 415 | 3 501 | ✓ 9 |
| 3 | max | `max` | 325 | **31 744** | 0 | 255 | 575 | 4 636 | ✓ 11 |
| 4 | low | `low` | 296 | **32 000** | 0 | 184 | 450 | 3 548 | ✓ 15 |
| 5 | ultracode | **`xhigh`** | 339 | **32 256** | 0 | 161 | 415 | 3 578 | ✓ 6 |

(The `tools:0` `<session>` context call that precedes turn 1 is NOT a main turn — excluded.)

## Findings

1. **The effort value reaches the wire and is accepted.** `output_config.effort` =
   high/xhigh/max/low on each turn — DeepSeek's Anthropic-compatible endpoint does not
   reject the field. All five slider positions landed, including max (session-only) and
   ultracode.
2. **`ultracode` sends `xhigh` on the wire — confirmed empirically.** Turn 5's request
   carries `output_config.effort: "xhigh"`, and its history shows CC injected the
   "Ultracode is on: optimize for the most exhaust…" context block. Matches the docs; now
   measured on the DeepSeek path too. (Consistency check: turns 2 and 5 — both wire-xhigh —
   show identical `think_chars: 415`.)
3. **DeepSeek's context cache is effort-AGNOSTIC — the headline difference vs Anthropic.**
   On Anthropic, switching effort is a cache-key dimension: the first visit to a new level
   cold-misses and rebuilds the whole prefix (`reports/thinking-cache.md`). Here, every
   switch (xhigh → max → low → ultracode) kept `cache_read` ~31–32k — **even the first-ever
   visits to xhigh/max/low**, which on Anthropic would be cold. No cache partition, no
   rebuild: switching effort on DeepSeek costs **zero cache tokens**. Consistent with the
   known quirk that DeepSeek's cache is silent (`cache_creation_input_tokens: 0` always —
   judge by `cache_read` alone).
4. **Effort barely changes model behavior on this probe.** Output tokens (235→173→255→
   184→161), thinking chars (549→415→575→450→415) and latency (6.7s→3.5s→4.6s→3.5s→3.6s)
   vary but **non-monotonically** — max had the most thinking/output, but low ≈ xhigh, and
   high (the cold turn) was slowest. The reply text is structurally identical across all
   levels ("Day N. After N−1 full day-night cycles the snail is at…"). All 5 answers
   correct. No "higher effort ⇒ deeper reasoning" signal at this difficulty.
5. **Thinking is streamed but not block-enumerated.** Responses carry a `thinking` delta
   (~400–575 chars, persisted into the next request's assistant history) but DeepSeek does
   not list content blocks in `message_start`, so `thinkingBlocks` reads 0 while
   `thinkingChars` (from `content_block_delta.type=thinking_delta`) is populated.

**Caveats.** A single-step arithmetic probe may be too easy to expose effort differences —
DeepSeek-v4-pro solves it at every level in a few seconds. A genuinely hard or long-running
agentic task could diverge. One run; the non-monotonic deltas are within noise.

## Harness learnings (why the first attempts failed)

- **VS Code onboarding gate:** a child launched from a VS Code terminal inherits `VSCODE_*`
  + `TERM_PROGRAM=vscode` and pops a "Welcome to Claude Code for VS Code — Press Enter to
  continue" modal on first launch in a fresh config dir — a dialog that can appear AFTER
  `ready()` and swallow the next Enter. Fixed in the driver: strip `VSCODE_*`/`TERM_PROGRAM`
  from `childEnv` + extend `ready()`'s dialog regex.
- **One-shot `send(text+'\r')` can swallow the Enter** on 2.1.226 (text lands in the input
  box, no request starts). Fixed: type → wait for the input-box echo → press Enter
  separately, then verify the request actually started by polling the capture (retry:
  bare Enter, then Esc-and-retype).
- **TUI echo matching word-concatenates:** the alt-screen renders spaces as cursor-forward
  escapes, so `stripAnsi` turns "deep well" into "deepwell" — `waitOutput(/deep well/)`
  never fires. Match with `\s*` between words (or a single word); keep the spaced token for
  the JSON capture, which has real spaces.
- **`setEffort` result-line capture is flaky** (the "Set effort level to X" line did not
  appear within the window for max/low/ultracode even though the switch landed — verified by
  the wire values). Made confirmation best-effort; the trace is the source of truth.
- **Exclude the `tools:0` `<session>` context call** from turn matching — it carries the
  probe text in a `<session>` block and would otherwise be miscounted as the main turn.
