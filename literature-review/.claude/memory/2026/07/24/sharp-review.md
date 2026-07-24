---
name: sharp-review-2026-07-24
description: Sharp review findings — 6 total
metadata:
  type: project
---

## Review 2026-07-24 (session) — security audit (安全锐评) + diff review

### Reviewer Status
- Reviewer A (Codex): FAILED
- Reviewer B (DeepSeek): skipped
- Reviewer C (Opus): OK
- Warning: only 1/2 reviewers succeeded

### Confirmed findings

---

### [SR-20260724-001] [HIGH] literature_review/providers/arxiv.py — arXiv Atom namespace has a typo (www.w3.org.org), so entry parsing silently returns zero records

- **Category:** Bug
- **Status:** FIXED (2026-07-24, same session)
- **Confidence:** single-reviewer
- **Suggestion:** Fix ARXIV_NS to "http://www.w3.org/2005/Atom".

Line 32 defines `ARXIV_NS = "http://www.w3.org.org/2005/Atom"` (doubled `.org`). Every record field is parsed via `entry.find(f"{{{ARXIV_NS}}}...")` and entries via `root.findall(f"{{{ARXIV_NS}}}entry")`. The real Atom namespace is `http://www.w3.org/2005/Atom`, so findall matches nothing and `_parse_atom` returns `records: []` while still reporting a non-zero `total_count` (that check is namespace-agnostic). The arXiv provider therefore yields totals but zero candidates — a completely broken, silent failure. No test caught it because tests use fake providers.

---

### [SR-20260724-002] [MEDIUM] literature_review/providers/base.py — max_retries is declared on BaseProvider and overridden in S2 but never used — no retry logic exists

- **Category:** Bug
- **Status:** FIXED (2026-07-24, same session)
- **Confidence:** single-reviewer
- **Suggestion:** Either implement a retry loop honoring max_retries/request_delay around _api_get on rate_limited/network_error, or delete the dead attribute and its overrides.

base.py adds `max_retries: int = 3` and semantic_scholar sets `max_retries = 2`, with a docstring promising retries for transient failures. The attribute is referenced nowhere. Both S2 and arXiv `_api_get` raise `ProviderError("rate_limited")` immediately on HTTP 429. Advertised retry behavior is fiction; on the S2 free tier queries will simply fail.

---

### [SR-20260724-003] [MEDIUM] literature_review/providers/arxiv.py — ArxivProvider sets no request_delay despite documenting a 1-request-per-3-seconds polite limit

- **Category:** Bug
- **Status:** FIXED (2026-07-24, same session)
- **Confidence:** single-reviewer
- **Suggestion:** Set `request_delay = 3.0` on ArxivProvider (as semantic_scholar does).

Module docstring states "Rate limit: one request per 3 seconds (polite delay)", but the class never sets `request_delay`, so it inherits `None`. run_probe/run_search gate their sleeps on `getattr(provider, "request_delay", None)`, meaning arXiv is hammered with no delay across pages/queries — risking 429s or IP bans, and with no retry those failures are terminal.

---

### [SR-20260724-004] [LOW] literature_review/pipeline/orchestrator.py — evaluate_queries output is written per-provider but never consumed — full search no longer receives evaluation_path

- **Category:** Feature
- **Status:** FIXED (2026-07-24, same session)
- **Confidence:** single-reviewer
- **Suggestion:** Either wire per-provider refinement suggestions back into _run_search, or drop the evaluate step to save API calls.

Previously `_run_search(..., evaluation_path=...)` fed refinement suggestions into the full search. The rewrite runs `evaluate_queries` into `evaluation/<provider>/` but the new full-search loop omits `evaluation_path` entirely, so the probe-evaluation stage produces artifacts nothing reads.

---

### [SR-20260724-005] [LOW] literature_review/pipeline/orchestrator.py — Redundant extra sleep after each provider probe on top of run_probe's per-query delay

- **Category:** Performance
- **Status:** FIXED (2026-07-24, same session)
- **Confidence:** single-reviewer
- **Suggestion:** Drop the orchestrator-level `_time.sleep(delay * 0.5)`; run_probe already sleeps request_delay per query. Move `import time` to module top.

The probe loop adds an arbitrary extra half-delay after each provider; the comment even admits per-query delay is already inside run_probe. Function-body `import time as _time` is needless churn.

---

### [SR-20260724-006] [INFO] literature_review/pipeline/orchestrator.py — run_search docstring claims default provider 'ieee' but code defaults to ['ieee_xplore'] from workspace.toml

- **Category:** Bug
- **Status:** FIXED (2026-07-24, same session)
- **Confidence:** single-reviewer
- **Suggestion:** Align the docstring with the actual default and note workspace.toml override precedence.

Signature docstring says default 'ieee', but resolution reads `ws_data.get('providers', ['ieee_xplore'])`. The alias forms and stated default disagree.
