---
name: proxy-profile-pitfalls
description: observe-proxy harness lessons — capture-based turn sync, FABLE env leak, proxy haiku-tier remap blind spot, stale shared-path default
created: 2026-07-17
tags: [driver, observe-proxy, pitfalls, deepseek]
---

# observe-proxy profile pitfalls (learned 2026-07-17)

1. **`waitIdle` races slow upstreams.** It fires during TTY-quiet streaming gaps; prompts
   sent afterwards queue in the TUI and never reach the wire (first ds-env run lost 3 of 4
   turns). Sync turns via evidence layer 1: poll `<runDir>/http.jsonl` for the request whose
   last user message carries the turn's token and has a paired response/error row.
2. **FABLE env leak.** `ANTHROPIC_DEFAULT_FABLE_*` is NOT in cc-market's
   `PROVIDER_ENV_KEYS`, so in proxy mode it leaks from the parent's `process.env` into the
   child (`childEnv` starts from `process.env`; `buildChildEnv` only strips listed keys).
   Sanitize `process.env` before `launch()` when a run needs those vars absent.
3. **Proxy haiku-tier blind spot.** The observe proxy's `resolveModelFromId` falls back to
   the opus default for non-Claude ids — a child sending `deepseek-v4-flash` (title-gen)
   gets remapped to `deepseek-v4-pro[1m]`. The proxy profile cannot observe haiku-tier
   routing for provider-native ids; direct-connect ccds is unaffected.
4. **Stale shared-path default.** `observe-reader.mjs` / `observe-proxy.mjs` /
   `spawn-child.mjs` live in `cc-market/fabric/engine` — the driver's default
   `.../cc-market/shared` no longer contains them; pass `CC_MARKET_SHARED=.../fabric/engine`.

Repo rule (user instruction 2026-07-17, now in AGENT.md Conventions): **AGENT.md holds
development principles only; experiment findings live solely in `reports/<name>.md`.**
