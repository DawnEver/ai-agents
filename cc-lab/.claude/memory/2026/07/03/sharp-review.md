---
name: sharp-review-2026-07-03
description: Sharp review findings — 51 total
metadata:
  type: project
---





## Review 2026-07-03 (session) — diff review + adversarial review (对抗性审查)

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): skipped
- Reviewer C (Opus): OK

### Confirmed findings

---

### [SR-20260703-001] [HIGH] cc-lab/cases/thinking-cache.case.mjs — The thinking-cache case does not assert the behavior it claims to test.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Make the case load its own tap records after close and fail unless it finds the two intended main turns, verifies the effort switch, and checks the expected cache_read/cache_creation relationship.

Lines 69-72 print DONE and tell a human to analyze the trace later. That means the command can exit successfully with a null tap session, the wrong turns, no cache invalidation, or a changed UI path as long as the PTY choreography did not throw. This is not a test; it is a manual probe with a success-looking exit.

---

### [SR-20260703-002] [MEDIUM] cc-lab/driver/tap.mjs — messages() is too broad and will mix main turns with auxiliary Messages API calls.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a stricter helper for main user turns, e.g. require status 200, usage, Array.isArray(system), non-empty tools, and optionally match the submitted user text.

isMessages only checks that request.path includes /v1/messages and response.status is 200. AGENT.md itself warns that title-gen and classifier calls can also be 200 Messages calls. Any future assertion using messages(records)[0], counts, model, tools, usage, or cache tokens can silently inspect the wrong request.

---

### [SR-20260703-003] [MEDIUM] cc-lab/driver/tap.mjs — Trace rehydration silently drops missing blob fields.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Throw if a compact record references a blob hash that is absent or cannot be parsed, including the path/hash in the error.

rehydrate skips a missing blob with `if (raw !== undefined)`. The whole harness treats tap data as authoritative evidence, so returning a partially rehydrated record is poisonous: tools/messages/system can be absent or truncated while downstream assertions still pass against incomplete data.

---

### [SR-20260703-004] [MEDIUM] cc-lab/driver/driver.mjs — close() can return before the child has actually exited and before tty.log is flushed.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** After term.kill(), wait for the exit event up to a second timeout and wait for the ttyLog finish/close event before resolving. If the process still does not exit, report that explicitly.

If Ctrl-D does not exit within graceMs, close() calls term.kill() and immediately returns exitCode, which is still likely null. The exit handler is what ends tty.log, so callers that immediately stat/read logs or query traces are racing process shutdown and stream flushing.

---

### [SR-20260703-005] [LOW] cc-lab/driver/driver.mjs — Model argument detection only handles the split --model form.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Detect both `--model value` and `--model=value`, or stop accepting model through claudeArgs and force callers to use the model option.

The injection guard checks `claudeArgs.includes('--model')`. A caller using the common `--model=...` form gets a duplicate model flag prepended. Depending on Claude Code's parser, that can select the wrong model or fail in a non-obvious way.

---

### [SR-20260703-006] [LOW] cc-lab/package.json — The package declares no Node engine even though it imports node:sqlite.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add an engines.node constraint matching the Node version that provides the required node:sqlite API, and document it in AGENT.md or package scripts.

driver/tap.mjs imports `DatabaseSync` from `node:sqlite`, which is not available in older Node versions. Without an engine guard, contributors can install dependencies successfully and then get a runtime module failure when running the cases.

---

### [SR-20260703-007] [HIGH] cc-lab/driver/driver.mjs — onData can write to an already-ended tty.log stream after child exit, and the WriteStream has no 'error' handler — either path throws an uncaught, process-killing exception

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Guard the write (`if (!exited) ttyLog.write(d)` or only end the stream after a final drain), and attach `ttyLog.on('error', …)`. Consider ordering: node-pty may deliver buffered onData *after* onExit.

onExit calls `ttyLog.end()`, but node-pty is not guaranteed to stop firing onData before/at exit — buffered PTY data can arrive after the exit event, and `ttyLog.write(d)` on an ended stream throws 'write after end'. Independently, `createWriteStream` with no 'error' listener will crash the whole harness on any I/O failure (disk full, path locked by OneDrive sync, EBUSY on Windows). Because the driver is the top-level process for a case, an unhandled stream error aborts the run with no diagnostic and leaves the child claude-tap process orphaned.

---

### [SR-20260703-008] [HIGH] cc-lab/driver/driver.mjs — The output buffer grows unbounded and every poll re-runs stripAnsi + regex over the entire accumulated buffer, giving O(n²) CPU and unbounded memory for long/verbose sessions

- **Category:** Performance
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Cap the buffer (keep only a trailing window, e.g. last 64KB, mirroring the `slice(-2000)` trick already used in ready()), and/or strip ANSI incrementally. waitOutput/ready/tapSessionId scanning should match against a bounded tail, not the full history.

`buffer += d` never trims. waitOutput (every 100ms), ready (every 200ms) and the tapSessionId matcher (every onData) all call `stripAnsi(buffer)` over the *whole* buffer. A verbose Claude turn produces megabytes of VT escapes; scanning grows linearly per poll and quadratically overall. A truly long-running case can exhaust memory or stall the event loop. This is a resource-exhaustion blind spot masked by the trivial prompts used so far.

---

### [SR-20260703-009] [HIGH] cc-lab/driver/driver.mjs — waitIdle assumes the TUI goes silent, but Claude Code's status bar / spinner / cursor blink repaint periodically — lastOutputAt keeps refreshing, so waitIdle can never reach its quiet window and falsely times out

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Treat pure cursor-motion / status-bar repaints as 'idle' by filtering them out of lastOutputAt updates, or key idle detection off content changes in the stripped buffer rather than raw byte arrivals. At minimum document that quietMs must exceed the TUI's repaint interval.

waitIdle returns only after `quietMs` with zero pty output. A real interactive TUI emits animation frames (thinking spinner during a turn, blinking cursor/clock at the prompt). Every frame bumps `lastOutputAt`, resetting the quiet timer. With quietMs=4000 this happens to work only because the animation cadence is slower — a faster spinner or a periodic redraw makes waitIdle hang until the 90s hard timeout and throw, which the cases surface as a spurious failure. This is the core race between 'no bytes' and 'turn actually finished' that the driver never validates.

---

### [SR-20260703-010] [MEDIUM] cc-lab/driver/driver.mjs — send()/key() write to the PTY with no guard against an exited/closed child, so any input after the child dies throws an uncaught exception

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Wrap term.write in send/key with the same try/catch (or exited check) that close() already uses, and surface a clear 'child already exited' error instead of a raw node-pty throw.

close() carefully guards `term.write('\x04')` in try/catch, but send() and key() do not. If the child crashes mid-case — OOM, auth expiry, a 5xx storm — the next `s.send(...)` throws a low-level EIO/'pty destroyed' error that bypasses the case's own timeout/assertion logic. Overconfidence that the child is always alive between primitives.

---

### [SR-20260703-011] [MEDIUM] cc-lab/driver/driver.mjs — ready() blindly presses Enter on any dialog matching a hard-coded token list, assuming the default option is always safe/affirmative — a wrong or reordered default silently mis-answers a gate

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Match the specific affirmative option text and navigate to it explicitly, or assert the expected dialog shape before answering. Also bound the number of Enter presses so a persistent/unrecognized dialog can't be spammed.

The DIALOG regex only knows trust-folder / external-imports dialogs, and the comment asserts 'each such dialog defaults to the safe/affirmative option'. That's an unverified assumption about CC's evolving TUI: a new gate whose default is a different option would be auto-confirmed wrongly. Worse, if a matched dialog does NOT clear within 1200ms the loop re-fires `\r` every iteration, potentially injecting stray Enters into the session once the dialog does clear.

---

### [SR-20260703-012] [MEDIUM] cc-lab/driver/driver.mjs — tapSessionId is captured opportunistically from stdout and never required before ready() returns; if the 'Trace session' line format changes or is missed, the session proceeds and only fails much later in loadRecords

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Make ready() (or a dedicated step) fail fast if tapSessionId is still null once the prompt is up, with a message pointing at the claude-tap startup banner, rather than deferring the failure to loadRecords('tapSessionId is required').

ready() waits for 'shortcuts', not for the trace-session line. The regex `/Trace session:\s*([0-9a-f-]{36})/i` is the sole capture point; if claude-tap changes its banner, buffers it after 'shortcuts', or the line is split across onData chunks, tapSessionId stays null. The whole trace-based evidence layer then collapses at loadRecords with a generic error, far from the real cause.

---

### [SR-20260703-013] [MEDIUM] cc-lab/driver/tap.mjs — loadRecords opens the trace DB immediately, but claude-tap may still be flushing the final turn's rows when close() returns — the reader can miss the last records or hit a Windows write lock

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** After close(), poll loadSession until record_count stabilizes (or the session row is marked complete) before asserting, and/or retry the read on SQLITE_BUSY. Don't assume close() implies a fully-persisted trace.

close() sends Ctrl-D and waits for exit of the PTY, but claude-tap's DB writes are asynchronous to the TTY teardown; on the smoke path the assertions run right after close(). There is a race where the last /v1/messages row isn't committed yet or, on Windows, the file is briefly locked and the readOnly open throws 'database is locked'. No stabilization or retry is present.

---

### [SR-20260703-014] [MEDIUM] cc-lab/driver/driver.mjs — close() relies on Ctrl-D then term.kill(), which kills claude-tap but may orphan the nested claude process (and its subprocesses), leaking processes across many runs

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Kill the whole process tree (on Windows, taskkill /T; on POSIX, kill the process group), and verify the child is actually gone after grace. Log a warning if kill() was needed so leaks are visible.

The tree is PTY → claude-tap → claude (→ possible tool subprocesses). Ctrl-D targets the foreground claude REPL; if claude is mid-turn or ignores EOF, the grace loop expires and term.kill() signals only claude-tap. On Windows especially, node-pty's kill does not reliably reap grandchildren. Across a test suite this leaks claude/claude-tap processes that keep holding the trace DB and credentials copy.

---

### [SR-20260703-015] [MEDIUM] cc-lab/driver/driver.mjs — Host credentials (.credentials.json) are copied into .lab/<run>/config inside a OneDrive-synced directory, exposing live auth tokens to cloud sync despite being gitignored

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Place run dirs (or at least the copied credentials) outside the OneDrive-synced tree — e.g. os.tmpdir() or a local, non-synced path — and/or clean up the credential copy on close. Gitignore does not stop OneDrive from uploading it.

The repo root is under 'OneDrive - The University of Nottingham'. copyFileSync writes real Claude credentials into absRunDir/config/.credentials.json. `.lab/` is gitignored (so it won't hit git) but OneDrive still syncs it to institutional cloud storage, and the copy is never deleted. A silent security tradeoff: credential material replicated to N cloud copies per run.

---

### [SR-20260703-016] [LOW] cc-lab/driver/tap.mjs — rehydrate/setByPath silently drops blob fields when a ref path is missing, and JSON.parse on a corrupt blob throws uncaught — either way assertions can run on incomplete records without warning

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Log or throw when a declared ref cannot be spliced (missing path or missing blob hash), and wrap JSON.parse in try/catch to fail with the offending hash. Don't let a partial rehydration masquerade as a complete record.

setByPath returns silently if an intermediate key is null, so a tools/messages blob referenced by the compact record can vanish and summarize() then reports tools:[] — a false 'no tools' signal that could quietly invalidate a case's conclusion. Separately, `JSON.parse(raw)` assumes every blob payload is well-formed JSON; a truncated/corrupt blob crashes loadRecords with an opaque SyntaxError.

---

### [SR-20260703-017] [LOW] cc-lab/driver/driver.mjs — waitOutput reuses a caller-supplied RegExp with .test(); a regex carrying the /g (or /y) flag is stateful, so repeated .test() calls advance lastIndex and can flakily never match

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Normalize incoming regexes by reconstructing without global/sticky flags (new RegExp(re.source, re.flags.replace(/[gy]/g,''))), or reset re.lastIndex=0 each poll.

`const re = regex instanceof RegExp ? regex : new RegExp(regex)` uses the caller's object as-is. If a case passes /pattern/g, `re.test(stripAnsi(buffer))` mutates lastIndex between polls; against a growing buffer this produces intermittent, hard-to-reproduce match failures.

---

### [SR-20260703-018] [LOW] cc-lab/cases/smoke.case.mjs — Run directories are keyed by an ISO timestamp truncated to seconds; two runs (or parallel cases) starting in the same second collide into one dir with mkdir recursive silently merging state

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a random/pid suffix or use higher-resolution/monotonic uniqueness for run dir names to guarantee isolation.

`new Date().toISOString()....slice(0,19)` yields second granularity. cc-lab is designed to run many cases; two launches in the same wall-clock second produce identical runDir, mkdirSync({recursive:true}) reuses it, and the second run's config/credentials/tty.log overwrite or interleave with the first — undermining the 'each run gets a fresh isolated config dir' invariant.

---

### [SR-20260703-019] [LOW] cc-lab/driver/driver.mjs — spawn() failure (claude-tap not found / not executable) is not handled — resolveClaudeTap falls back to a bare 'claude-tap' on PATH and a missing binary surfaces as an unhandled async error

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Validate the resolved tap path or attach an error handler to the spawned term and reject launch() with an actionable message ('claude-tap not found on PATH or ~/.local/bin').

If claude-tap isn't installed, resolveClaudeTap returns 'claude-tap' and node-pty spawn will fail asynchronously; there's no term.onError/try-catch, so the case dies with a cryptic ENOENT far from the cause.

---

### [SR-20260703-020] [INFO] cc-lab/cases/thinking-cache.case.mjs — The /effort case hard-codes 'two steps left from high' and specific picker/confirm strings, coupling a headline finding to one CC build's exact TUI wording and slider layout

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Assert the actual landed effort level from the trace before drawing conclusions, and treat picker/confirm string matches as best-effort with explicit failure messages if the UI changed. Consider reading the slider state rather than assuming positional moves.

The report's conclusion depends on turn 2 being at a *different* effort than turn 1. The case achieves that by blind positional key presses and matching `/to adjust|Faster|Smarter/` and `/switch to|Change effort level/i`. If a future build reorders the slider, changes defaults, or reworks the confirmation copy, the case may silently confirm at the same level (no cache bust) or hang — and the recorded finding would be quietly wrong.


## Review 2026-07-03 (follow-up)

## Review 2026-07-03 (session) — architecture survey (架构锐评) + diff review

### Reviewer Status
- Reviewer A (Codex): skipped
- Reviewer B (DeepSeek): OK
- Reviewer C (Opus): FAILED
- Warning: only 1/2 reviewers succeeded

### Confirmed findings

---

### [SR-20260703-021] [HIGH] cases/thinking-cache.case.mjs — Case files embed assertion logic, violating the planned separation of concerns.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Strip all assertion code from case files; make them pure I/O drivers and leave analysis to the parent Claude.

The architecture states 'Analysis is NOT code: the parent Claude reads the trace files and writes findings to reports/'. However, thinking-cache.case.mjs and env-var-matrix.case.mjs inline FAIL/ok checks and custom mainTurns filters. This mixes test logic with PTY interaction, causing duplication, tight coupling, and making cases difficult to reuse or run non-interactively.

---

### [SR-20260703-022] [MEDIUM] cases/btw-isolation.case.mjs — Duplicate type() helper, stamp pattern, and mainTurns filter across multiple case files.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Create a shared library (e.g., lib/case-utils.mjs) for common driver helpers, run naming, and trace filters.

The type() method (with retry logic) is reimplemented in both btw-isolation.case.mjs and output-style-layer.case.mjs. The ISO timestamp stamp is repeated in every case file. env-var-matrix.case.mjs reimplements mainTurns filtering instead of using driver/tap.mjs exports. This duplication increases maintenance burden and risks divergence.

---

### [SR-20260703-023] [MEDIUM] cases/smoke.case.mjs — No test framework; hand-rolled assertions and exit-code management are inconsistent across cases.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Adopt a lightweight test runner (e.g., Node built-in node:test) with a standard assert library for all cases.

smoke.case.mjs uses a custom assert() that sets process.exitCode, while other cases have no structured error handling. This leads to inconsistent failure reporting, harder debugging, and no way to aggregate results. A single test harness would centralize logging and cleanup.

---

### [SR-20260703-024] [MEDIUM] cases/btw-isolation.case.mjs — Inconsistent error handling and cleanup across case files, risking resource leaks.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Enforce a standard try-finally block in every case that calls driver.close() and cleans up child processes.

Some cases lack proper finally blocks or early-exit handling, leaving PTY processes dangling on error. driver.mjs already guards against double-close, but a missing close() call can cause zombie processes and log corruption in the isolated config directories.

---

### [SR-20260703-025] [LOW] driver/driver.mjs — Driver module approaching the 300-line complexity threshold with mixed concerns.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** If the module grows, split it into submodules: pty-wrapper.mjs, config-bootstrap.mjs, and credential-scrubber.mjs.

At 291 lines, driver.mjs manages PTY lifecycle, config setup, and credential scrubbing. These are distinct responsibilities that could be separated to improve testability and readability as the project evolves.

---

### [SR-20260703-026] [LOW] driver/tap.mjs — Polling-based loops in tap.mjs retry on SQLITE_BUSY and wait for trace files.

- **Category:** Performance
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Polling is acceptable for a local CI-like tool; no change needed unless resource usage becomes an issue.

loadRecords uses a polling retry loop, and waitForTrace polls for file existence. For an experiment harness running on-demand, this is low-risk. If future workloads require many concurrent runs, an event-driven or callback-based approach would be more efficient.

---

### [SR-20260703-027] [INFO] AGENT.md — Architecture docs, conventions, and pitfalls are combined in a single file nearing the 100-line threshold.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** If the file grows beyond 100 lines, split into docs/ARCHITECTURE.md and docs/CONVENTIONS.md for clarity.

AGENT.md (92 lines) serves as a catch-all for architecture descriptions and developer guidelines. While still under the recommended limit, separating concerns now would prevent a future monolithic doc and align with the project own separation philosophy.


## Review 2026-07-03 (follow-up)

## Review 2026-07-03 (session) — docs review (文档锐评)

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): skipped
- Reviewer C (Opus): skipped

### Confirmed findings

---

### [SR-20260703-028] [MEDIUM] AGENT.md — AGENT.md still tells readers to read trace files even though the current driver/tap code uses the shared claude-tap sqlite database as the authoritative trace source.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Replace the 'reads the trace files' wording with instructions to read the trace DB through driver/tap.mjs, matching the rest of AGENT.md and the current code.

The Evidence section correctly says intercepted requests are rows in ~/.local/share/claude-tap/traces.sqlite3 and not files under --tap-output-dir, and driver/tap.mjs implements loadRecords/mainTurns against that sqlite DB. Later, the Conventions section says 'the parent Claude reads the trace files and writes findings', which reintroduces the removed file-based workflow and contradicts both the code and earlier documentation.

---

### [SR-20260703-029] [LOW] cases/smoke.case.mjs — The smoke case header documents a stale assertion that tap/ contains trace files, but the code now asserts against the trace DB.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update the file comment to say the smoke case captures a tap trace-session id and loads records from the shared sqlite DB; do not mention tap/ trace files.

The header says the test 'asserts: tap/ got at least one trace file and tty.log is non-empty'. The implementation instead asserts s.tapSessionId is present, calls loadRecords(s.tapSessionId), and checks /v1/messages records. This stale comment can mislead contributors into looking for per-run trace files that claude-tap no longer writes.

---

### [SR-20260703-030] [MEDIUM] AGENT.md — The alternate-screen warning contradicts the current env-var report and case evidence, which classify CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN as a no-op in this build.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Revise the pitfall to match the verified behavior: in cc 2.1.199 under this PTY harness the variable did not toggle classic alternate-screen rendering; warn that rendering assumptions should be re-verified per build instead of stating it changes rendering.

AGENT.md says 'CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN=1 eases debugging but changes rendering'. reports/env-var-matrix.md says CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN produced no tty-structure difference and was a no-op here, and cases/env-var-matrix.case.mjs explicitly tests for ESC[?1049h. The root guidance is therefore stale for the current codebase findings.

---

### [SR-20260703-031] [LOW] reports/system-prompt-anatomy.md — The Sources section references reports/system-prompt-anthropic.json, but that file is not present and the current capture case writes system-prompt.json under .lab/<run>/ instead.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Either add the referenced JSON artifact to reports/ or change the source note to the actual generated path from cases/system-prompt-diff.case.mjs.

rg --files shows no reports/system-prompt-anthropic.json. The current capture script cases/system-prompt-diff.case.mjs writes the extracted prompt to .lab/<run>/system-prompt.json. As written, the report points readers to a missing artifact.

---

### [SR-20260703-032] [LOW] AGENT.md — Setup and usage instructions omit required prerequisites and runnable commands for a fresh checkout.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a short setup section covering Node >=22.5, npm install, claude-tap availability/PATH, authentication expectations, and example commands such as node cases/smoke.case.mjs and npm run clean.

package.json declares node >=22.5 and depends on node-pty; driver/driver.mjs requires claude-tap to be installed or available in ~/.local/bin/PATH and bootstraps credentials from CLAUDE_CONFIG_DIR or ~/.claude. AGENT.md describes architecture and conventions but does not tell a new contributor how to install dependencies or run the smoke case, leaving setup implicit in code.


## Review 2026-07-03 (follow-up)

## Review 2026-07-03 (session) — docs review (文档锐评)

### Reviewer Status
- Reviewer A (Codex): OK
- Reviewer B (DeepSeek): skipped
- Reviewer C (Opus): skipped

### Confirmed findings

---

### [SR-20260703-033] [MEDIUM] AGENT.md — AGENT.md still references a file-based trace workflow that contradicts the current sqlite-backed driver.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Replace the Conventions wording about reading trace files with reading the shared claude-tap sqlite DB through driver/tap.mjs.

The Evidence section and driver/tap.mjs agree that claude-tap records live in ~/.local/share/claude-tap/traces.sqlite3 and are loaded via loadRecords/mainTurns. But AGENT.md later says the parent Claude reads 'trace files', which points contributors back to the removed per-run trace-file model.

---

### [SR-20260703-034] [LOW] cases/smoke.case.mjs — The smoke case header documents stale tap/ trace-file assertions.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update the header to say the smoke test captures a tap trace-session id, loads records from the shared sqlite DB, and checks tty.log.

The comment says the case asserts 'tap/ got at least one trace file', but the implementation asserts s.tapSessionId, calls loadRecords(s.tapSessionId), and checks Messages records from the trace DB. claude-tap's --tap-output-dir is no longer the authoritative output location.

---

### [SR-20260703-035] [MEDIUM] AGENT.md — The alternate-screen warning contradicts the current env-var evidence.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Revise the pitfall to state that CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN was a no-op in cc 2.1.199 under this PTY harness and that UI-render assumptions must be re-verified per build.

AGENT.md says CLAUDE_CODE_DISABLE_ALTERNATE_SCREEN=1 eases debugging but changes rendering. reports/env-var-matrix.md and cases/env-var-matrix.case.mjs classify it as a no-op here, checking for ESC[?1049h and finding no tty-structure difference.

---

### [SR-20260703-036] [LOW] reports/system-prompt-anatomy.md — The Sources section points to a missing JSON artifact.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Either commit the referenced reports/system-prompt-anthropic.json or change the source note to the actual generated .lab/<run>/system-prompt.json path from cases/system-prompt-diff.case.mjs.

rg --files shows no reports/system-prompt-anthropic.json. The current capture driver writes system-prompt.json inside the run directory, so the report's source reference is broken.

---

### [SR-20260703-037] [MEDIUM] .claude/memory/2026/06/03/progress.md — The progress memory says M3 and M4 are pending even though the repository now contains those cases and reports.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update the PLAN status to mark btw-isolation, output-style-layer, env-var-matrix, and prompt-anatomy/system-prompt analysis as completed, with links to the current files.

progress.md claims M3 behavior cases and M4 prompt-anatomy are pending. The repo now has cases/btw-isolation.case.mjs, cases/output-style-layer.case.mjs, cases/env-var-matrix.case.mjs, reports for each, and prompt/system anatomy reports.

---

### [SR-20260703-038] [MEDIUM] .claude/memory/2026/06/03/PLAN.md — The implementation plan preserves outdated hypotheses and setup expectations as if they were still current.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a status note or retire the stale plan sections after moving verified facts into AGENT.md and reports.

PLAN.md still instructs the smoke test to assert tap/ contains trace files, says thinking should be toggled with Tab pending verification, hypothesizes /btw carries no tools, and targets output-style switching. Current code and reports refute or replace each of those items.

---

### [SR-20260703-039] [LOW] .claude/rules/MEMORY.md — The generated memory index omits an existing memory entry.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Rebuild the memory index so .claude/memory/2026/07/03/manual.md is listed, or document why manual task files are intentionally excluded.

.claude/memory/2026/07/03/manual.md exists and has valid frontmatter, but .claude/rules/MEMORY.md lists sharp-review, PLAN, and progress only. That makes the memory index incomplete for the current repository state.

---

### [SR-20260703-040] [LOW] AGENT.md — Setup and usage instructions are still implicit despite package and driver prerequisites.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a short setup section covering Node >=22.5, npm install, claude-tap availability, authentication source, node cases/smoke.case.mjs, and npm run clean.

package.json declares Node >=22.5 and node-pty; driver/driver.mjs requires claude-tap on PATH or ~/.local/bin and bootstraps credentials from CLAUDE_CONFIG_DIR or ~/.claude. AGENT.md explains architecture well but does not give a fresh contributor a runnable path.


## Review 2026-07-03 (follow-up)

## Review 2026-07-03 (session) — docs review (文档锐评)

### Reviewer Status
- Reviewer A (Codex): skipped
- Reviewer B (DeepSeek): OK
- Reviewer C (Opus): skipped

### Confirmed findings

---

### [SR-20260703-041] [HIGH] .claude/memory/2026/06/03/progress.md — Progress tracker claims M3 behavior cases and M4 prompt-anatomy are PENDING, but all six cases and both anatomy reports exist in the repo.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update PLAN status to DONE for M3 and M4 with links to current files.

Lines 21-22 state M3 and M4 are PENDING. The repo actually contains all six cases and both anatomy reports plus the system-prompt-diff capture case.

---

### [SR-20260703-042] [HIGH] .claude/memory/2026/06/03/PLAN.md — Implementation plan preserves multiple hypotheses empirically refuted by experiments, with no status update.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a status header noting which hypotheses were refuted, or retire plan sections after moving verified facts into AGENT.md.

Three stale claims: thinking toggle described as Tab key (refuted — it is /effort); /btw hypothesis of no tools (refuted); smoke test assert described as per-run trace files (refuted — uses SQLite DB).

---

### [SR-20260703-043] [MEDIUM] AGENT.md — Conventions section says parent reads trace files which contradicts the Evidence section describing the SQLite trace DB.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Replace reads the trace files with reads the trace DB via driver/tap.mjs to match the Evidence section.

Line 57 says reads the trace files but lines 20-25 correctly state traces live in the SQLite DB and are read via loadRecords/messages/summarize.

---

### [SR-20260703-044] [MEDIUM] AGENT.md — DISABLE_ALTERNATE_SCREEN pitfall claims the variable changes rendering but env-var-matrix report classifies it as a no-op.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Revise the pitfall to match verified behavior: under this PTY harness the variable produced no difference; warn that assumptions should be re-verified per build.

Lines 78-79 warn the variable changes rendering but env-var-matrix found byte-identical tty output with and without it.

---

### [SR-20260703-045] [MEDIUM] AGENT.md — No setup, prerequisite, or usage instructions exist.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a Setup section covering Node >=22.5, npm install, claude-tap availability, authentication, example command, and cleanup.

AGENT.md describes architecture and pitfalls but never tells a reader how to install, authenticate, or run the smoke test.

---

### [SR-20260703-046] [MEDIUM] reports/system-prompt-anatomy.md — Sources section references reports/system-prompt-anthropic.json which does not exist.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Commit the referenced JSON or change the source note to the actual output path.

Line 125 lists the JSON as a source but no such file exists; the capture script writes to .lab/<run>/system-prompt.json.

---

### [SR-20260703-047] [MEDIUM] .claude/rules/MEMORY.md — Memory index omits .claude/memory/2026/07/03/manual.md which has valid frontmatter.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Rebuild the memory index so manual.md is listed.

The Entries section lists sharp-review.md, PLAN.md, and progress.md but not manual.md despite valid frontmatter.

---

### [SR-20260703-048] [LOW] AGENT.md — Pitfalls main-turn isolation heuristic is missing system.length >= 3 check that mainTurns() requires.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update lines 89-90 to match mainTurns() exactly by adding the system.length >= 3 condition.

The docs say Array.isArray(system) plus tools and usage but driver/tap.mjs mainTurns() additionally requires system.length >= 3.

---

### [SR-20260703-049] [LOW] cases/smoke.case.mjs — Header comment says the case asserts tap/ got trace files but the actual code asserts against the SQLite trace DB.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update the header comment to match the actual assertions.

Lines 3-4 claim tap/ trace file assertions but the code checks tapSessionId, loadRecords, messages, and tty.log size.

---

### [SR-20260703-050] [LOW] driver/driver.mjs — Cases duplicate the run-name stamp pattern instead of using the drivers exported runDirName() utility.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Update all case files to use runDirName() from driver/driver.mjs.

All six cases independently implement their own stamp pattern; none imports runDirName().

---

### [SR-20260703-051] [INFO] AGENT.md — Foundry env-var stripping behavior in driver.mjs is undocumented.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Add a note to Pitfalls about env var stripping so claude-tap can intercept traffic.

Driver deletes Foundry-related env vars from childEnv before spawn, which is load-bearing for claude-tap interception but is never documented.
