---
name: download-architecture-refactor
description: PDF acquisition audit and phased refactor — typed ledger, transport capability ladder, matcher removal
created: 2026-07-26
metadata:
  type: design
tags: [architecture, acquire, download, refactor, plan]
---

# Download Architecture — Audit and Refactor Plan

Scope: the PDF acquisition path only (`acquire/*`, `pipeline/acquire.py`, the acquire
step of `pipeline/orchestrator.py`). Other pipeline stages are owned elsewhere.

## Baseline (pre-refactor, 2026-07-26)

2035 lines across the acquire surface:

| Module | LOC | Role | Tests |
|---|---|---|---|
| `acquire/download.py` | 842 | browser driver + transport + orchestration + log | partial |
| `pipeline/acquire.py` | 473 | queue + PDF match + manifest (**no networking**) | none |
| `acquire/researchgate.py` | 264 | RG search → publication → download | yes |
| `acquire/oa_resolve.py` | 188 | DOI → OA locations, source ranking | yes |
| `acquire/http_fetch.py` | 149 | browser-free fetch, landing-page link extraction | yes |
| `acquire/crawl.py` | 118 | dead code, no callers | none |

## Confirmed defects

1. **Manifest path mismatch → ingest unreachable.** `match_pdfs` writes
   `topic_dir/pdf_match/match_report.json` (`pipeline/acquire.py:379`); the orchestrator
   reads `topic_dir/download/pdf_match/match_report.json` (`orchestrator.py:316`). The
   branch never fires, so `download_manifest.json` is never written and `run_ingest`
   (which requires it) cannot be reached. Every observed run printed `manifest=None`.
   Already flagged in the 2026-07-23 sharp-review; survived because
   `pipeline/acquire.py` has zero test coverage.
2. `_download_with_page` is 221 lines / 9 strategies / 8 returns / 8 raises. Cookie-banner
   dismissal sits at line 400, *after* the button click at line 282 that it exists to
   unblock — and the common path returns before reaching it.
3. `_maximum_weight_matching` is O(2^n) in approved items, with an all-or-nothing
   ambiguity rule that discards the entire matching.
4. Two `validate_pdf` with different semantics: `download.py` checks the magic bytes only;
   `pipeline/acquire.py` also requires >=1024 bytes. A 300-byte stub passes download and
   is rejected at manifest time.
5. `semantic_scholar.py` omits `openAccessPdf` from `SEARCH_FIELDS`, though
   `oa_resolve.py:155` already requests exactly that field. OA links are discarded at
   search time and re-queried per DOI at download time.
6. Three HTTP stacks (`requests`, `urllib.request`, Playwright `context.request`) and two
   Playwright drivers; `acquire_headed` (~170 lines) has no caller.
7. Dead `oa_url` key; `maybe` items queued but never auto-approved; `limit=20` hardcoded
   and equal to `HARD_LIMIT`; CLI defaults `chrome` while `run_acquire` defaults `chromium`.

## First principles

The job: **given a paper's identity, produce a verified PDF or an honest reason why not.**
Four sub-problems with different failure modes and different testability:
identity→locations (pure, cacheable), locations→bytes (effectful, capability-tiered),
bytes→verified artifact (pure), and what-happened (append-only ledger). The current code
entangles all four, which is why the browser paths are untestable — and untestability is
why defects 1-3 survived.

- **A — Transport is a capability ladder, not an if-chain.** Cost order: plain HTTP →
  browser-context request → browser navigation → site-specific driver. Filter by the
  capability the host actually requires.
- **B — Failures must be typed.** `Blocked` (retryable), `Denied` (IP-level, circuit-break),
  `NotOpenAccess` (terminal), `NotFound`, `Malformed` warrant different behaviour. The RG
  breaker proved this but hardcoded it as a special case.
- **C — The matcher should not exist.** `acquire_pdfs` knows which paper each file belongs
  to (it names the file `<cid>_<title>.pdf`), discards that, and `match_pdfs` then extracts
  PDF text and runs exponential maximum-weight assignment to *re-infer* the same mapping.
  Only user-dropped `manual_drop/` files genuinely need matching.

## Target layout

```
acquire/
  refs.py         PaperRef (doi/title/candidate_id/known URLs)
  resolve/        identity -> ranked Source list  (oa.py, ranking.py)
  transport/      Source -> bytes: base.py protocol, http.py, browser.py, researchgate.py
  verify.py       the single validate_pdf / sha256 / safe_filename
  ledger.py       DownloadRecord append; the downstream source of truth
  engine.py       orchestration: for ref -> for source -> for transport
```

Types in `models.py`: `Source(url, rank, needs)`,
`DownloadRecord(candidate_id, status, pdf_path, sha256, source_url, attempts)`,
`Outcome = DOWNLOADED | BLOCKED | DENIED | NOT_OPEN_ACCESS | NOT_FOUND`.

Ledger becomes the contract: `match_pdfs` leaves the main flow, `write_download_manifest`
reads the ledger, and matching survives only as a simple by-DOI/filename lookup for
`manual_drop/`.

## Phases

Each phase leaves the pipeline runnable.

- **Phase 0 — stop the bleeding.** Fix the manifest path + cover `pipeline/acquire.py`
  with tests; delete `acquire_headed`, `crawl.py`, the `oa_url` key (~300 lines); unify
  `validate_pdf` on the strict semantics; add `openAccessPdf` to S2 `SEARCH_FIELDS`;
  align CLI/orchestrator defaults; expose `limit`.
- **Phase 1 — typed core.** `Outcome`/`DownloadRecord`/`Source`; ledger lands; typed
  failures replace strings.
- **Phase 2 — decompose transport.** Split the 221-line function into the capability
  ladder; the ordering bug dissolves (banner dismissal becomes a browser-transport
  precondition). Browser adapter shrinks to ~50 lines; everything else unit-testable.
- **Phase 3 — delete the matcher.** Manifest reads the ledger; `manual_drop` takes the
  simple path. Removes O(2^n) and the implicit ~25-paper ceiling.
- **Phase 4 — unify HTTP policy.** One session/timeout/UA/backoff layer; providers move
  off `urllib`.
- **Phase 5 — observability.** `--dry-run` prints the per-paper Source plan with no
  network, turning "why did this not download" into an up-front question.

## Outcome (all phases executed 2026-07-26)

Delivered as planned. Verified end-to-end on the CHP workspace: `downloaded=1` and — for the
first time — a real `handoff/download_manifest.json`, so `run_ingest` is reachable.

Two defects the refactor itself surfaced, both fixed:

- `page.on("download", list.append)` raised `'builtin_function_or_method' object has no
  attribute '_pw_impl_instance_'`. Playwright stores bookkeeping attributes on the handler,
  and a builtin method has no `__dict__`. Handlers must be real functions.
- Transports returning `None` recorded no attempt, so the log under-reported and a paper with
  a valid DOI was described as having "no candidate URL". Every attempt is now recorded.

Live finding: Cloudflare tightened on `research-information.bris.ac.uk`. An out-of-band
`context.request` to the file endpoint is refused (403) even though navigating the tab to the
same URL returns 200. The browser transport now intercepts `page.on("response")` and takes
whatever the tab actually received — the mechanism the deleted `acquire_headed` had used. The
clearance-cookie retry alone no longer suffices.

Known and deferred by the user: ResearchGate returns Cloudflare error 1020 (IP ban) for this
network. The circuit breaker handles it correctly; the ban itself is a future fix.

## Notes

- Phase 0 is independent and net-positive on its own; do it regardless.
- Phase 3 changes where `handoff/download_manifest.json` comes from, but since that file
  is currently never produced, the regression surface is smaller than it looks.
- `pipeline/acquire.py` should be renamed (`queue.py` + `manifest.py`) — it contains no
  networking and the name is the source of the confusion.
- Do not add scipy for the matcher; Phase 3 removes it outright.
