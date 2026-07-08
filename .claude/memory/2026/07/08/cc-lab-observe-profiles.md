---
name: cc-lab-observe-profiles
tier: short
created: 2026-07-08
---

# cc-lab driver observe profiles (commit cf3a4a8)

`launch({observe: 'tap'|'proxy'|'none', provider})` added to `cc-lab/driver/driver.mjs`:

- `'tap'` (default) — claude-tap MITM as before; the Foundry env strip is now **tap-mode
  only** (it exists because tap can't intercept Foundry routing).
- `'proxy'` — borrows the cc-market fabric engine layer (`Sync/claude/cc-market/shared`,
  override `CC_MARKET_SHARED`): plain `claude` under the PTY, vanilla env via
  `buildChildEnv`, capture in `<runDir>/http.jsonl` (`session.jsonlPath`), read with the
  shared `observe-reader.mjs`. Validated live against DeepSeek —
  `cases/observe-proxy-profile.case.mjs`.
- `'none'` — direct-connect, env untouched.

Two `close()` fixes shaken out by the live run:

1. **Double Ctrl-D**: recent CC builds require a second Ctrl-D within a short confirm
   window ("Press Ctrl-D again to exit"). close() sends the pair 250ms apart and retries
   the pair across the grace period. A single Ctrl-D (or a pair spaced >~1s) never exits.
2. **node-pty handle teardown**: after a clean child exit, the conin/conout sockets + the
   ConoutConnection worker keep the node event loop alive. `term.kill()` releases them but
   spawns `conpty_console_list_agent`, which crashes noisily ("AttachConsole failed") on an
   already-exited child. Fix replicates `agent.kill()`'s teardown minus the
   console-process-list step: destroy `_inSocket`/`_outSocket`, dispose
   `_conoutSocketWorker`, `_ptyNative.kill` (private API, node-pty 1.x).

Note: claude-tap is not installed on this machine (DUIPEZZTZ) — tap-mode cases only run on
devices that have it; the proxy profile has no such dependency.
