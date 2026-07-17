# deepseek-model-env-cache

**Question.** Does the "legacy" DeepSeek model-env layout — `ANTHROPIC_MODEL` +
tier defaults + `CLAUDE_CODE_SUBAGENT_MODEL`, **no** `*_SUPPORTED_CAPABILITIES` —
still cause multi-turn prompt-cache misses on the current Claude Code build
(2.1.212), vs the ccds layout (tier defaults + `FABLE` + `SUPPORTED_CAPABILITIES`)?
The user hit cache misses with the legacy layout on an older build and switched to
the ccds layout.

**Answer. No — both layouts cache fine on cc 2.1.212.** The old cache-miss issue is
not reproducible. Configurations are equivalent for caching; the ccds
`SUPPORTED_CAPABILITIES` set is not required for cache health (it only governs which
CC features — thinking/effort UI — are enabled for the tier).

## Setup

`cases/deepseek-model-env-cache.case.mjs`, observe profile `'proxy'` (provider
`deepseek`), two interactive sessions, identical 4 trivial user turns
(`Reply with exactly: ALPHA/BRAVO/CHARLIE/DELTA`). Turn sync polls the proxy capture
(`http.jsonl`) for the request carrying each turn's token — `waitIdle` races ahead of
a slow upstream and queues the remaining prompts (first run lost 3 of 4 turns to this).

Env hygiene note: in proxy mode the driver's `childEnv` starts from `process.env`, and
`ANTHROPIC_DEFAULT_FABLE_*` is NOT in cc-market's `PROVIDER_ENV_KEYS`, so a parent
running ccds would leak its FABLE vars into the legacy run. The case deletes every
provider-ish var from `process.env` before launching.

## Data (run dirs `.lab/2026-07-17T22-57-06-ds-env-legacy-29851`, `…22-57-27-ds-env-ccds-29851`)

Conversation turns only (title-gen is a 1-message tool-free call, excluded):

| turn | legacy: input / cache_read | ccds: input / cache_read |
|------|---------------------------|--------------------------|
| 1 (ALPHA)   | 29427 / **0** (cold, creates cache) | 29428 / **0** (cold) |
| 2 (BRAVO)   | 128 / **29312** | 129 / **29312** |
| 3 (CHARLIE) | 141 / **29312** | 14  / **29440** |
| 4 (DELTA)   | 26  / **29440** | 27  / **29440** |

Identical cache behavior in both configs: first turn cold, every subsequent turn reads
~29.3k tokens from cache. DeepSeek reports `cache_creation_input_tokens: 0` even when
it (silently) populates its context cache — a miss on this endpoint shows as
`cache_read: 0`, not as a creation charge.

The legacy request shape is already cache-friendly: system blocks carry `ephemeral`
breakpoints, the last user message carries one, and `thinking: {"type":"adaptive"}` is
sent **even without** `SUPPORTED_CAPABILITIES`.

## Side observations

- **Proxy remap artifact (not CC behavior):** the observe proxy's `resolveModelFromId`
  falls back to the opus-tier default for non-Claude ids, so the title-gen request
  (child sent `deepseek-v4-flash`) was remapped to `deepseek-v4-pro[1m]` in BOTH runs.
  In real direct-connect ccds use, the haiku tier reaches `deepseek-v4-flash` untouched.
  Harmless here, but it means the proxy profile cannot observe haiku-tier routing for
  provider-native ids.
- The legacy layout's `ANTHROPIC_MODEL=deepseek-v4-pro[1m]` pins the main tier
  directly; the ccds layout relies on tier defaults. Both arrive at the same upstream
  model per turn.

## Conclusion

On cc 2.1.212, the legacy env block has no cache problem — if the user wants to revert
to it (e.g. to pin `CLAUDE_CODE_SUBAGENT_MODEL`), caching is not a reason to avoid it.
The historical miss was likely a CC build that sent different `thinking`/effort fields
without declared capabilities, or a DeepSeek endpoint behavior that has since changed.
