---
name: deepseek-model-env-cache
description: legacy DeepSeek model env (ANTHROPIC_MODEL + tier defaults, no SUPPORTED_CAPABILITIES) caches identically to the ccds layout on cc 2.1.212 — historical cache miss not reproducible
created: 2026-07-17
tags: [deepseek, prompt-cache, model-env, observe-proxy, cc-2.1.212]
---

# deepseek model env: legacy layout caches fine on cc 2.1.212

Case `cases/deepseek-model-env-cache.case.mjs`, report `reports/deepseek-model-env-cache.md`,
commit `1744602`. Two interactive sessions via observe-proxy (provider deepseek), 4 trivial
turns each, turn-sync by polling `http.jsonl`.

## Finding

Both env layouts cache identically — turn 1 cold (~29.4k input, cache_read 0), turns 2+
read 29312–29440 from cache:

- **legacy**: `ANTHROPIC_MODEL=deepseek-v4-pro[1m]` + tier defaults + `CLAUDE_CODE_SUBAGENT_MODEL`, NO `*_SUPPORTED_CAPABILITIES`
- **ccds**: tier defaults + `ANTHROPIC_DEFAULT_FABLE_*` + `*_SUPPORTED_CAPABILITIES`

The user's historical multi-turn cache miss with the legacy layout is **not reproducible**
on cc 2.1.212. `SUPPORTED_CAPABILITIES` only gates CC features (thinking/effort UI), not
cache health — legacy requests already carry `cache_control: ephemeral` breakpoints and
`thinking: {"type":"adaptive"}`.

- DeepSeek endpoint **always reports `cache_creation_input_tokens: 0`** — it silently
  populates its context cache; a miss shows as `cache_read: 0` only. Judge cache health by
  `cache_read` alone.
- Title-gen etc. are 1-message tool-free calls; filter conversation turns by
  `tools.length > 0` or the (correctly cold) title turn pollutes assertions.
