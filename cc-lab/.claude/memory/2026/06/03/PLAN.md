# cc-lab Implementation Plan

Goal: a cross-platform (Windows + macOS) harness where a parent Claude drives a **real
interactive Claude Code** session through a PTY, `claude-tap` captures every API request,
and the parent Claude analyzes the traces to answer research questions.

Read `AGENT.md` first — it fixes the architecture, evidence-layer philosophy, and pitfalls.
Core principle: **the TUI is only an input channel; assertions live in the tap trace and
session files, never in screen-scraping.**

## Prerequisites (already verified on this machine)

- `claude-tap` 0.1.126 installed via `uv tool install claude-tap`
  (at `~/.local/bin/claude-tap`; NOT the unrelated `claude-tap` npm package).
  Key flags: `--tap-no-open --tap-no-live --tap-output-dir <dir> -- <claude args>`.
- `node-pty` ^1.1.0 declared in `package.json` — run `npm install` and verify the
  prebuild loads (Windows ConPTY). If the native module fails, that is the first
  blocker to solve before anything else.

## Milestone 1 — driver (`driver/driver.mjs`)

A thin ESM module exporting `launch(opts) -> session`. Keep it to five primitives.

```js
const s = await launch({
  runDir,            // e.g. .lab/2026-07-03-thinking-cache
  claudeArgs = [],   // forwarded after `--`
  env = {},          // merged over process.env
  cols = 140, rows = 40,
});
s.send(text)                        // pty.write(text + '\r')
s.key(seq)                          // raw escape sequences: '\t', '\x1b', '\x04'
await s.waitOutput(regex, timeout)  // poll accumulated pty buffer
await s.waitIdle(quietMs, timeout)  // no pty output for quietMs → turn likely done
await s.close()                     // Ctrl-D, grace period, then kill
```

Responsibilities inside `launch`:

1. Create `runDir/tap/` and `runDir/config/`.
2. **Bootstrap the isolated config dir** so the child skips onboarding and is
   authenticated:
   - copy `.credentials.json` from the real config dir (`$CLAUDE_CONFIG_DIR` or
     `~/.claude`) if it exists (macOS may use keychain — then skip; claude-tap
     handles auth detection);
   - write `<configDir>/.claude.json` with `{"hasCompletedOnboarding": true}` plus a
     theme, so the first-run wizard never blocks the PTY.
3. Spawn via node-pty (`name: 'xterm-256color'`):
   `claude-tap --tap-no-live --tap-no-open --tap-output-dir <tap> -- <claudeArgs>`
   with `CLAUDE_CONFIG_DIR=<configDir>` in env. On Windows resolve
   `claude-tap.exe` from `~/.local/bin` if not on PATH.
4. Tee all pty output to `runDir/tty.log` and an in-memory buffer for `waitOutput`.

Smoke test (TDD, before any case): a script that launches, waits for the input prompt,
sends "Say OK and nothing else.", waits idle, closes — then asserts `tap/` contains at
least one trace file and `tty.log` is non-empty. **Inspect the tap output format here
and document it in AGENT.md** (the README promises request/response/usage capture; the
on-disk layout must be discovered empirically).

## Milestone 2 — first real case: `cases/thinking-cache.case.mjs`

Question: does toggling thinking mode mid-session break prompt-cache hits?

Script: launch → send trivial msg → waitIdle → toggle thinking (Tab key in current
builds — verify in tty.log which keybinding actually toggled it) → send second trivial
msg → waitIdle → close → print run dir.

Analysis (done by the parent Claude, written to `reports/thinking-cache.md`):
compare consecutive requests' `usage` (`cache_read_input_tokens`,
`cache_creation_input_tokens`, `input_tokens`) and diff `system` / `thinking` fields.
Deliverable: a clear statement of which cache breakpoints survive the toggle.

## Milestone 3 — behavior cases (each = one case file + one report)

1. **btw-isolation** — while the main turn is running, send `/btw …`; assert from the
   trace: a separate request exists, it carries no `tools`, and later main-thread
   requests exclude the /btw Q&A.
2. **output-style-layer** — switch output style, diff the `system` array across
   requests to show exactly which block changes (and whether cache survives).
3. **env-var matrix** — rerun a minimal scenario under selected env vars
   (`CLAUDE_CODE_FORCE_SESSION_PERSISTENCE`, subagent model vars, …) and classify
   each as: startup-config / API-request / tool-env / UI-render layer.

## Milestone 4 — prompt-anatomy report

From accumulated traces, map the system prompt: stable prefix (cacheable), per-session
variance, and segments never referenced by behavior (candidates for "useless prompt"
findings). Pure analysis, no new code.

## Out of scope (tracked elsewhere)

- Session cost break-even (new vs continued session, per-model DeepSeek/Claude
  configs) → traceme, offline analysis of historical session jsonl `usage` fields.
- Chinese-vs-English capability e2e → reuses this harness later; raw-API half needs
  no harness at all.

## Working rules for the executing agent

- TDD: smoke test before driver features; every case must fail meaningfully if the
  child never responds (timeouts, not hangs).
- Windows first (this machine), keep macOS paths in mind (`claude-tap` binary name,
  keychain auth); no tmux, no Python drivers.
- Costs real tokens: keep case prompts trivial ("Say OK"), one run per question.
- Findings go to `reports/`; update AGENT.md when an empirical fact (tap format,
  thinking keybinding) is confirmed.
- Commit per milestone in the `agents` repo, conventional messages.
