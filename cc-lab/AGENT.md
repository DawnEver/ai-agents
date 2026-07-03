# cc-lab

Experiment harness for observing Claude Code behavior: a parent Claude drives a real
interactive Claude Code session through a PTY, with `claude-tap` capturing every API
request. Cross-platform (Windows ConPTY / macOS forkpty via node-pty).

## Architecture

```text
parent Claude (designs cases, runs driver, reads traces, writes reports)
  └── node cases/<name>.case.mjs
        └── node-pty → claude-tap --tap-no-live --tap-no-open … -- claude
              (isolated CLAUDE_CONFIG_DIR per run)
```

## Evidence layers (assert on the structured ones)

1. **API trace** — authoritative for cache hits, system prompt diffs, /btw requests,
   tools schema, token usage. Primary assertion target. **NOT** written as files into
   `--tap-output-dir` (that flag is a legacy one-shot *import* dir). Every intercepted
   request/response is a row in the shared sqlite DB
   `~/.local/share/claude-tap/traces.sqlite3`, keyed by the tap **trace-session UUID**
   (the `Trace session: <uuid>` line printed at startup — captured by the driver as
   `session.tapSessionId`, distinct from Claude Code's own `X-Claude-Code-Session-Id`).
   Read it via `driver/tap.mjs` (`loadRecords` / `messages` / `summarize`).
   - Each record payload: `{ request_id, turn, duration_ms, request:{method,path,
     headers,body}, response:{status,headers,body} }`.
   - `request.body` carries `model`, `system` (array of blocks), `tools`, `messages`,
     `thinking`. `response.body.usage` carries `input_tokens`, `output_tokens`,
     `cache_read_input_tokens`, `cache_creation_input_tokens`.
   - Filter real turns with `isMessages` — the client also fires a `max_tokens:1`
     `content:"quota"` probe to `/v1/messages?beta=true` that returns **404**; skip it.
2. **Persisted state** (`.lab/<run>/config/`) — session jsonl, what enters history.
3. **TTY** (`.lab/<run>/tty.log`) — unstructured, version-fragile. Input channel and
   sync points only; never the primary assertion target. The TUI renders spaces as
   cursor-forward escapes, so `stripAnsi(buffer)` yields **word-concatenated** text:
   match single tokens, never multi-word phrases.

## Findings (see `reports/`)

- **thinking-cache** — switching `/effort` fully busts the prompt cache (server-side
  cache-key dimension; body byte-identical).
- **btw-isolation** — `/btw` is a separate request, forward-isolated from main history,
  but carries the full tools + main history (not tool-free); steered by a system-reminder.
- **output-style-layer** — output styles are removed in this build; a `/goal` directive
  layers into the **message** history (not system prompt) and the cache survives.
- **env-var-matrix** — `CLAUDE_CODE_MAX_OUTPUT_TOKENS` = API-request layer,
  `…FORCE_SESSION_PERSISTENCE` = state layer; the two `DISABLE_*` vars are no-ops here.
- **prompt-anatomy** — tools+identity (~37.5k tok) cache cross-session; the 15.8 KB
  instruction block is cache-orphaned per session by two embedded path lines (cwd +
  scratchpad UUID); dynamic context lives in the message layer.

## Conventions

- One experiment = one `cases/<name>.case.mjs`, self-executing, prints its run dir.
- Analysis is NOT code: the parent Claude reads the trace DB via `driver/tap.mjs`
  and writes findings
  to `reports/<name>.md`. Driver stays a thin primitive API
  (`send` / `key` / `waitOutput` / `waitIdle` / `ready` / `close`); `ready()` clears
  the startup gate dialogs (folder-trust, external-CLAUDE.md-imports) that appear on
  first launch in a fresh config dir and waits for the input prompt.
- Each run gets a fresh `.lab/<timestamp>-<name>/` with isolated `CLAUDE_CONFIG_DIR`
  (credentials + onboarding state bootstrapped by the driver). `.lab/` is gitignored.
- **`.lab/` is disposable — clean it after analysis.** Authoritative traces live in the
  shared claude-tap sqlite DB (keyed by tap-session UUID, which reports reference), not
  in `.lab/`; the run dir only holds `tty.log` (dev-only) and the isolated config. Since
  the repo sits under a **cloud-synced tree**, a live `.credentials.json` copy must not
  linger: `close()` scrubs it on exit (pass `keepCredentials:true` to retain), and
  `npm run clean` (`scripts/clean-lab.mjs`, supports `--days N` / `--creds`) removes runs.
- **Cost control:** `launch()` defaults the child to **Haiku** (`--model`). Override
  per-case only when the question is genuinely model-specific, and prefer **Sonnet**
  over Opus. Never run cases on Opus just for convenience. Keep prompts trivial.

## Pitfalls

- Child sessions launched from a parent Claude Code get `CLAUDE_CODE_CHILD_SESSION=1`
  and are excluded from resume/history. Set `CLAUDE_CODE_FORCE_SESSION_PERSISTENCE=1`
  when simulating a normal user; leave it off when studying nested-session behavior.
- `CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN=1` was a no-op in cc 2.1.199 under this PTY
  harness — no TTY structure difference. UI-render assumptions must be re-verified
  per build; never assume a flag does what its name suggests.
- macOS keychain: `claude-tap` auto-detects auth; the driver's credential copy only
  applies where file-based credentials exist (Windows/Linux).
- **Thinking/effort is the `/effort` command, not Shift+Tab** (which cycles permission
  modes). `/effort` is a horizontal slider (←/→, Enter) + a Yes/No confirmation.
  Switching the effort level **fully invalidates the prompt cache** (server-side
  cache-key dimension) even though the request body is byte-identical — see
  `reports/thinking-cache.md`.
- Not every `/v1/messages` 200 is a main turn: the client also fires title-gen,
  classifier, and `max_tokens:1` "quota" (404) calls. Isolate main turns by
  `Array.isArray(system) && system.length >= 3 && tools.length > 0 && response.body.usage`
  present — match `mainTurns()` exactly.
- Records are stored **compact**: large fields (tools, big messages) are offloaded to
  the `record_blobs` table and the payload is nested under `.record`. `loadRecords`
  rehydrates them — always read traces through `driver/tap.mjs`, never raw SQL.
