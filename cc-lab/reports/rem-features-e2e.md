# REM features e2e — remember.js + recall.js (commits 08df9db + b5017be)

Date: 2026-07-29 · Case: `cases/rem-recall.case.mjs` · Verdict: **ALL PASS**

Test target pinned via `REM_DEV_CLONE` to a worktree at `b5017be`
(the dev clone's working tree carried teammates' in-flight edits — see Bugs).

## Observation setup (host constraints discovered)

- `claude-tap` was not installed on this macOS host — installed via
  `uv tool install claude-tap` (PyPI, `liaohch3/claude-tap`).
- tap profile cannot auth here: isolated `CLAUDE_CONFIG_DIR` cannot use the
  macOS keychain, and the inherited `ANTHROPIC_API_KEY` is a Kimi key
  (`ANTHROPIC_BASE_URL=api.kimi.com`). Child reported "Not logged in".
- So Part B ran with `observe: 'proxy'` (deepseek upstream, model
  `deepseek-v4-flash`), capture in `<runDir>/http.jsonl` via
  `fabric/engine/observe-reader.mjs`. (The driver's default engine path was
  stale — `cc-market/shared/`; fixed in driver + cases on 2026-07-29 and
  verified by running `observe-proxy-profile.case.mjs` with no override.)
- Child env pins required: `ANTHROPIC_API_KEY=''` (avoids custom-API-key
  approval dialog), `ANTHROPIC_MODEL=''`, `CODEX_HOME=''` (recall.js's
  `isCodexHost` treats any CODEX_HOME as Codex → silent exit),
  `TERM_PROGRAM=Apple_Terminal` (VS Code terminal makes the child show a
  "Welcome to Claude Code for VS Code" dialog that swallows prompts).

## Plugin seeding (how the child got the NEW code)

Pre-seeded the isolated config before `launch()`:

- `plugins/cache/cc-market/rem/<version>/` ← full copy of the pinned `rem/`
- `plugins/marketplaces/cc-market/.claude-plugin/marketplace.json` ← manifest copy
- `plugins/installed_plugins.json` (`rem@cc-market` → installPath)
- `plugins/known_marketplaces.json` (github source entry, `autoUpdate:false`)
- `settings.json` → `{"enabledPlugins": {"rem@cc-market": true}}`

Verified the seeded copy's `hooks/hooks.json` registers `recall.js` under
`UserPromptSubmit` before asserting (case assertion).

## Part A — remember.js e2e (no child) — PASS

Ran the pinned `remember.js` three times (`--scope <runDir>`):

- `golangbolo-prefs` (user), `zephyrine-freeze` (project), `sourdough-notes` (reference)

Asserted for each: file at `.claude/memory/YYYY/MM/DD/<slug>.md` with
frontmatter `name`/`description`/`metadata.type` and NO volatile fields;
`_meta.json` entry `{accessed: today, count: 1, tier: short}`;
`.claude/rules/MEMORY.md` index line. Overwrite guard: different body without
`--update` refused (exit 1, "file exists with different content"); with
`--update` succeeds. All assertions printed `ok`.

## Part B — recall.js hook in a real child session — PASS

Run dir: `.lab/2026-07-29T01-31-34-rem-recall-99669` (cleaned after analysis;
evidence quoted inline below).

- **Negative** (prompt: `what is 2 + 2?`, sent first): agent request req 3,
  200 — `auto-recalled` marker **absent** from the entire request; no memory
  body strings (`ZQD-7`, `MARROW`, `78 percent`) anywhere. Hook stayed silent.
- **Positive** (prompt: `what is my golangbolo testing preference? …`):
  agent request req 4, 200 — injection present, verbatim:

  ```
  UserPromptSubmit hook additional context: Relevant memories (auto-recalled):

  --- golangbolo-prefs (2026/07/29/golangbolo-prefs.md) ---
  The golangbolo test framework prefers table-driven tests executed with the ZQD-7 runner.
  ```

  Injected block names `golangbolo-prefs` and carries its body; the other two
  entries are NOT in the block. (Their names legitimately appear elsewhere in
  the request via the auto-loaded `.claude/rules/MEMORY.md` project-rules index
  — assertions were scoped to the injected block for this reason.)
- Earlier runs (8 consecutive child sessions, same harness) also showed the
  child ANSWERING from the recalled body ("…table-driven tests executed with
  the ZQD-7 runner") — the injection is consumed, not just attached.

## Harness pitfalls hit (for future cases)

- Auxiliary calls (title-gen/classifiers) repeat the prompt with `tools:0` —
  filter agent requests by `tools.length > 0` before token-matching.
- Don't wait for turn completion: deepseek child may go tool-happy and park on
  a TUI approval prompt. Assert on the first agent REQUEST (hook context is
  already in it); dismiss dialogs with Escape (deny), never approve.
- The second `send()`'s `\r` is intermittently swallowed (text sits in the
  composer) — retry Enter until the request appears (`sendAndCapture`).
- TTY turn-end verbs are randomized ("Worked/Cooked/Baked for Ns") — poll the
  capture, not the screen.

## Bugs found

1. **Working tree only (not the pinned commits), since resolved:** `rem/scripts/lib.mjs`
   imported `atomicWriteFile` from `rem/shared/stamp.mjs` before the bundled copy
   exported it — a transient broken window between the stamp.mjs update and the
   shared/ rebundle; every rem script died at import. lock-agent confirmed the
   rebundle landed (500 pass / 0 fail), and a **re-run of this case against the
   fixed working tree PASSED in full** (run `.lab/2026-07-29T01-37-40-rem-recall-9468`),
   also covering recall-agent's CJK-bigram tokenizer + candidate cache and
   remember-agent's nested `metadata:` / `type:` frontmatter (the case's type
   assertion accepts both the flat `metadata.type:` and nested forms).
2. No bugs in the committed recall.js / remember.js behavior itself.

## Skipped (per task brief)

- rem-hook.js null session_id fix — unit-tested upstream.
- prune feedback exemption + locking — unit-tested, low e2e value.
- Stop-hook /rem gate — not exercised (would need a 3-stop session).
