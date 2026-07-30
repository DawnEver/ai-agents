---
name: sharp-review-2026-07-30
description: Sharp review findings — 8 total
metadata:
  type: project
---

## Review 2026-07-30 (session) — diff review + adversarial review (对抗性审查)

### Reviewer Status
- Reviewer claude (claude): OK
- Reviewer codex (codex): OK
- Reviewer deepseek (deepseek): skipped
- Reviewer kimi (kimi): skipped

### Confirmed findings

---

### [SR-20260730-001] [HIGH] literature-review/literature_review/pipeline/ingest.py — Backward-compat directory resolution matches by case-insensitive substring of candidate_id inside paper.md — trivially returns the wrong paper's directory

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Match on an explicit metadata field (e.g. a candidate_id key in INDEX.md front-matter or a sidecar json), or at minimum require a word-boundary/exact-token match. Better: run a one-time migration (rename old dirs to canonical CID names) in the new repair command instead of a fuzzy fallback on every lookup.

cid_lower in content.lower() over the first 4KB of paper.md is a substring test. A CID like 'P1' matches any paper.md containing 'p1', 'P10', 'p1000', or arbitrary prose/DOI text. Since ingest_output_dir is the single source of truth for cache checks, a false positive silently maps candidate A to candidate B's ingested text — the downstream reader will deep-read the wrong paper and treat it as cached with no error anywhere. iterdir() order is also filesystem-dependent, so with multiple partial matches the result is nondeterministic across platforms.

---

### [SR-20260730-002] [HIGH] literature-review/literature_review/acquire/transport.py — http_only is plumbed through hidden mutable global state (_browser_disabled) that is set but never reset, leaking across runs in the same process

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Pass http_only as an explicit parameter to default_transports(page, item, http_only=...) and to HttpTransport(accept_all=...). Delete the module-level toggle entirely; enable_browser() is dead code that admits the design is stateful.

acquire_pdfs(http_only=True) calls disable_browser() and never re-enables it — no try/finally, no reset. Any subsequent acquire_pdfs() call in the same interpreter silently runs http-only with no indication why browser sources are skipped. Test pollution is guaranteed: one test setting the flag poisons every later test. The parameter already threads cleanly from CLI to orchestrator to engine; smuggling the last hop through a global is a pure design regression.

---

### [SR-20260730-003] [MEDIUM] literature-review/literature_review/pipeline/orchestrator.py — Queue-reuse path prints a stale, contradictory message after rebuilding on sha mismatch, and silently trusts queues lacking screening_sha256

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Restructure: compute the mismatch first, set rebuild=True, and print the 'Queue exists with N items' line only when the existing queue was actually kept. Treat a missing screening_sha256 as 'cannot verify, rebuild' (or at least warn).

When screening_sha != current_sha the queue is rebuilt but execution falls through to print a line reporting the old queue's item count plus a --rebuild-queue hint that no longer applies. Worse, if the existing queue predates the screening_confirmation.screening_sha256 field, the staleness check is skipped entirely — the case where drift is most likely is never verified.

---

### [SR-20260730-004] [MEDIUM] literature-review/literature_review/pipeline/acquire.py — write_download_manifest default flipped to write_md=False — a silent behavioral change for every existing caller of the legacy path

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Audit all call sites and either keep the old default or update callers explicitly.

Only the orchestrator call site was updated to pass write_md=True. Any other caller — including the legacy Path source branch this function still supports, and presumably the new pipeline/repair.py — now silently stops producing download_manifest.md and its handoff-gate output. If a stale download_manifest.md from a previous run remains on disk, it silently disagrees with the fresh JSON.

---

### [SR-20260730-005] [MEDIUM] literature-review/literature_review/cli.py — repair --dry-run is a stub: prints one line and never invokes repair logic, contradicting its documented purpose

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Pass dry_run through: repair_workspace(td, dry_run=args.dry_run) and have the repair module report the planned actions.

The help text says dry-run should report what would be done, but _handle_repair prints only 'Would repair workspace: <path>' and returns — zero diagnostic value. A repair command that mutates the append-only ledger is exactly where a real dry-run matters most.

---

### [SR-20260730-006] [LOW] literature-review/literature_review/acquire/engine.py — plan_sources encodes http-only status by mangling the transport label string instead of adding a field

- **Category:** Feature
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Keep transport: 'http' and add a boolean like 'degraded': true. Format the warning in the CLI printer, not in the data.

transport = 'http (no-browser mode — will likely fail with challenge)' turns a machine-readable enum into prose. The CLI column formatting also breaks. Any future consumer of the plan structure has to string-match to distinguish real http from degraded http.

---

### [SR-20260730-007] [HIGH] literature-review/literature_review/acquire/engine.py — Process-global browser toggle is not reset after each acquisition, leaking state across calls in the same process

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Scope the browser toggle to the call or restore its previous value in a finally block instead of using module-level mutable state

After any acquire_pdfs(..., http_only=True) call, _browser_disabled remains enabled for the lifetime of the process. A subsequent normal acquisition still creates a browser page but default_transports() silently excludes browser and ResearchGate transports, causing publisher downloads to fail unexpectedly. This flag is module-level mutable state with no cleanup — test pollution is guaranteed, and any library-style reuse of acquire_pdfs will break silently.

---

### [SR-20260730-008] [HIGH] literature-review/literature_review/pipeline/repair.py — Repair creates incomplete canonical ingest directories that block future ingestion

- **Category:** Bug
- **Status:** OPEN
- **Confidence:** single-reviewer
- **Suggestion:** Preserve a mapping without creating the canonical directory, or migrate/link the complete ingest tree

When repairing a legacy title-based ingest, repair_workspace creates a canonical directory containing only a redirect-like paper.md, not the required PDF, index, and section files. Future ingestion treats any existing canonical directory as completed and skips it, while ingest_output_dir() returns this incomplete marker instead of the actual legacy directory.
