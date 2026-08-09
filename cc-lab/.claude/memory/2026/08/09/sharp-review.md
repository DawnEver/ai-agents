---
name: sharp-review-2026-08-09
description: Sharp review findings — 15 total
metadata:
  type: project
---

## Review 2026-08-09 (session) — diff review + adversarial review (对抗性审查)

### Reviewer Status
- Reviewer claude (claude): skipped
- Reviewer codex (codex): OK
- Reviewer deepseek (deepseek): OK
- Reviewer kimi (kimi): skipped

### Confirmed findings

---

### [SR-20260809-001] [HIGH] cc-lab/driver/driver.mjs — The new copyCredentials:false option is broken in the default tap mode

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Preserve an explicitly supplied API key when copyCredentials is false, or reject this incompatible combination with a clear error. Separate inherited provider variables from caller-supplied opts.env before sanitizing.

The option documentation says copyCredentials:false makes the child fall back to the inherited ANTHROPIC_API_KEY, but the tap branch unconditionally deletes ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN, and ANTHROPIC_BASE_URL after merging opts.env. In the default observe:'tap' mode this can leave the child with neither copied OAuth credentials nor API credentials. It also silently discards credentials explicitly supplied by the caller.

---

### [SR-20260809-002] [HIGH] cc-lab/cases/tui-vs-printloop.case.mjs — The Codex exec loop replays only the last 200 characters of each answer

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Keep the complete stdout reply in history and truncate only the separately persisted/displayed preview.

phaseCodexExecLoop defines reply as out...trim().slice(-200) and then appends that truncated value to history. Claude print-loop history retains the full answer, while Codex receives only a tail fragment. This violates the experiment's identical-history premise and can materially change turns 2 and 3.

---

### [SR-20260809-003] [HIGH] cc-lab/reports/tui-vs-printloop.md — The report labels Codex exec token totals as fresh tokens without measuring cache usage

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Parse each exec session's token_count events and report input, cached input, and output separately. Until then, describe tokens used only as an undifferentiated total and remove the no-cross-process-cache conclusion.

The case claims Codex exec usage comes from the stderr summary plus the session file, but phaseCodexExecLoop never reads its session files. The scalar 'tokens used' value does not establish that all tokens are fresh, so the claims that exec has no cross-process cache and that its fresh-token total is 28.1k are unsupported. Stable totals across processes are not evidence of cache absence.

---

### [SR-20260809-004] [MEDIUM] cc-lab/cases/tui-vs-printloop.case.mjs — Turn timeouts are treated as measurements instead of failed runs

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Throw immediately when a turn cannot be confirmed and make assert throw rather than merely setting process.exitCode. Persist partial usage with an explicit failed/incomplete status.

Both TUI phases log TIMEOUT and continue sending later turns. The final assert only sets process.exitCode, so usage.json and the summary are still emitted and can be mistaken for valid data. After a missed dispatch or token_count event, turn numbering and conversation state are no longer trustworthy.

---

### [SR-20260809-005] [MEDIUM] cc-lab/cases/tui-vs-printloop.case.mjs — Three phases use the async Promise executor anti-pattern

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Make phaseClaudePrintLoop, phaseCodexTui, and phaseCodexExecLoop plain async functions and return normally.

new Promise(async (resolvePhase) => ...) does not connect rejection of the async executor to the outer promise. Any spawn, trace, filesystem, or timeout error can become an unhandled rejection while the phase promise remains unsettled. The wrappers add no value and make failure behavior dependent on Node's unhandled-rejection policy.

---

### [SR-20260809-006] [MEDIUM] cc-lab/cases/tui-vs-printloop.case.mjs — The committed experiment is hard-coded to one user's Codex installation

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Resolve codex from PATH, accept a CODEX_CLI_PATH override, or reuse a shared executable resolver.

CODEX_JS is fixed to C:/Users/linxu/nodejs/node_modules/@openai/codex/bin/codex.js. The case cannot be reproduced by another user, on another platform, or after a Node installation layout change. The repository's driver already demonstrates the appropriate resolver/override pattern.

---

### [SR-20260809-007] [LOW] cc-lab/cases/tui-vs-printloop.case.mjs — The 356-line case duplicates infrastructure and should be decomposed

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Extract reusable process execution, polling, Codex session parsing, credential/environment shaping, and usage normalization into small driver modules; leave the case responsible only for defining turns and orchestrating modes.

The file exceeds the stated 300-line scrutiny threshold and mixes four runners, auth setup, environment filtering, PTY synchronization, filesystem crawling, parsing, assertions, persistence, and reporting. It duplicates driver behavior such as credential copying and provider-variable stripping, which has already drifted into contradictory semantics around copyCredentials.

---

### [SR-20260809-008] [MEDIUM] cc-lab/cases/tui-vs-printloop.case.mjs — Phase A undercounts TUI cost: [SUGGESTION MODE] background API calls bill real tokens but are filtered out of the measurement, while Phase B disables suggestions entirely.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Count suggestion-mode calls' usage in a separate 'suggestionCost' bucket (they're real paid requests) or disable suggestions in Phase A too, so A and B measure the same call set.

claudeRealTurns() drops any record whose system block contains 'SUGGESTION', but the report's own setup notes that background suggestion calls fire after every reply and consume real API usage. Phase B instead passes --prompt-suggestions false. So the TUI column omits a source of billed tokens that the -p column structurally avoids. The headline 'TUI bills 1.4x cheaper' is partly an artifact of not billing the TUI's suggestion calls. The developer treated suggestion calls as noise to filter rather than as a cost to account.

---

### [SR-20260809-009] [MEDIUM] cc-lab/driver/driver.mjs — The new env-strip (ANTHROPIC_BASE_URL/API_KEY/AUTH_TOKEN) in tap mode is unconditional with no opt-out, silently breaking existing tap cases that authenticated via the inherited x-api-key rather than copied OAuth file creds.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Gate the BASE_URL/API_KEY/AUTH_TOKEN strip behind the same flag that governs the credential copy (e.g. strip only when copyCredentials is true), or add a separate 'stripProviderEnv' option defaulting to true so env-key-authed tap setups can opt out.

copyCredentials:false only skips copying ~/.claude/.credentials.json; it does NOT stop the new regex from deleting ANTHROPIC_BASE_URL/ANTHROPIC_API_KEY/ANTHROPIC_AUTH_TOKEN from the child env. On any host where the only valid credential is the env key (no OAuth file — the driver explicitly skips the macOS keychain case), tap-mode children now become credential-free and fail auth. This is a behavior change applied to every existing tap-mode case, not just this one, and it cannot be disabled. The comment frames it as a fix for the deepseek gateway but never considers the setups that were relying on the env key.

---

### [SR-20260809-010] [MEDIUM] cc-lab/cases/tui-vs-printloop.case.mjs — Permission-mode asymmetry is a confound: Phase A runs the TUI under its default permission mode, Phase B forces --permission-mode bypassPermissions, which changes the system prompt and tool configuration and thus the measured tokens.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Run Phase A through launch() with the same --permission-mode bypassPermissions (or drop it from Phase B) so both claude modes share an identical system prompt; document the divergence if it must remain.

The case claims 'identical task' across modes but the two claude modes differ in permission mode. bypassPermissions injects extra permission instructions and different tool handling into the system prompt, which is a large fraction of the 42-49k token harness being measured. Any token difference between A and B is partly attributable to this flag, not the process-per-turn architecture the experiment claims to isolate.

---

### [SR-20260809-011] [MEDIUM] cc-lab/cases/tui-vs-printloop.case.mjs — Default ABCD run runs all phases back-to-back with no enforced cache-isolation, so the primary numbers are warm-cache and mode-order confounded (A warms B; A is coldest, B warmest).

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Make --phases=AB actually sleep >=5min between A and B by default, or emit a loud warning when running the full ABCD set that the cache-spacing requirement is not met; report cold-cache A/B numbers as the primary claim and relegate the back-to-back run to an appendix.

The report's own finding 4 concedes the 1-hour ephemeral tier keeps the shared prefix warm even across >=15-min 'cold' runs, and finding 3 shows a fully-warm -p run bills 0 creation. Yet the headline table comes from a single run where all 4 phases executed sequentially (A->B->C->D). B inherits A's cache warmth and D runs last. The code offers --phases for spacing but never enforces or even warns about the required gap; nothing stops someone from running default ABCD and reading the result as a cold comparison.

---

### [SR-20260809-012] [LOW] cc-lab/cases/tui-vs-printloop.case.mjs — Phase D reply extraction targets 'tokens used' on stdout, but the report documents that line is on stderr — so the regex never matches and the entire stdout becomes the next turn's history.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Trim the reply against the merged (out+err) stream or against the known codex prompt/exit framing, and only fall back to slice(-200) after confirming the match; assert the reply doesn't contain the token-count summary.

reply = out.replace(/.*?tokens used[\s\S]*$/i, '').trim().slice(-200). Because 'tokens used N' is on stderr (per the report's own measurement-setup note) and `out` is stdout only, the replace is a no-op and `reply` is the full stdout trimmed to the last 200 chars — which can include codex's status framing or echoed input. This polluted context is then replayed as 'Assistant: <reply>' into the next turn, slightly contaminating D's token measurement and breaking the clean history-repayment the mode is meant to model.

---

### [SR-20260809-013] [LOW] cc-lab/cases/tui-vs-printloop.case.mjs — totalTokenCount() sums token_count across every session file matching the cwd; a stale session left in that cwd by a prior aborted run makes waitTurn() short-circuit and the loop race ahead of actual dispatch.

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Snapshot the session-file baseline before the phase and only count new token_count entries above that baseline, rather than reducing over all files for the cwd.

codexSessionsForCwd returns all session files whose meta cwd equals the work dir, and totalTokenCount reduces over all of them. The work dir is derived from the timestamped runDir so it's usually fresh, but a re-run of phase C (--phases=C) in the same run dir, or a prior phase C that crashed before Ctrl-C, leaves a session file in place. The next run sees totalTokenCount() already >= min and every waitTurn resolves instantly, so turns are sent before the prior session is ready — flaky turns and wrong token counts. Nothing guards against this because the code assumes a pristine cwd.

---

### [SR-20260809-014] [LOW] cc-lab/cases/tui-vs-printloop.case.mjs — Watchdog uses process.exit(2) on a .unref()'d timer, which can orphan the PTY/codex/claude children and leave partial session files and usage.json mid-write.

- **Category:** Performance
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** On watchdog fire, signal children (kill the pty, SIGTERM the spawned -p/exec processes) before exiting, and write usage.json atomically (temp file + rename) so a kill mid-writeFileSync cannot corrupt it.

The 20-min watchdog calls writeUsage() then process.exit(2). At that moment codex/claude child processes and PTYs may be mid-turn; process.exit tears down the parent without cleaning them, potentially leaving an orphaned codex TUI and a half-written session jsonl. writeUsage() writes usage.json non-atomically, so a concurrent exit can truncate the very file the watchdog exists to protect.

---

### [SR-20260809-015] [INFO] cc-lab/cases/tui-vs-printloop.case.mjs — The report generalizes 'fabric's openWriteSession loses history' to a separate project (cc-market) from a single measured instance on one build (claude 2.1.226), without verifying it's a property of the code rather than the build.

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Reframe as 'observed on 2.1.226; verify against engine/session.mjs argv construction and other claude builds before acting on it as a defect'.

Finding 3 concludes fabric's history repayment 'is currently lost on this build' and calls its cost model 'wrong'. That is an out-of-scope, cross-repo claim based on one run. The newline-truncation behavior is plausibly real, but promoting a single measured observation into a stated defect of another codebase's design is overconfident until reproduced and traced to the actual argv handling.
