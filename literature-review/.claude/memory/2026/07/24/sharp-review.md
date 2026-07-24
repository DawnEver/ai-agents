---
name: sharp-review-2026-07-24
description: Sharp review findings — 22 total
metadata:
  type: project
---

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


## Review 2026-07-24 (follow-up)

## Review 2026-07-24 (session) — diff review + adversarial review (对抗性审查)

### Reviewer Status
- Reviewer A (Codex): skipped
- Reviewer B (DeepSeek): OK
- Reviewer C (Opus): OK

### Confirmed findings

---

### [SR-20260724-007] [HIGH] literature_review/providers/base.py — _search_with_retries catches bare Exception, so permanent failures (bad API key, malformed query, 400/403) are retried with exponential backoff

- **Category:** Bug
- **Status:** FIXED (2026-07-24, same session)
- **Confidence:** single-reviewer
- **Suggestion:** Retry only transient errors: catch ProviderError with a transient reason, or network/timeout/429/5xx exceptions. Re-raise everything else immediately. Also log each retry attempt instead of sleeping silently.

The docstring says 'exponential backoff on transient errors' but the code is `except Exception`. For ArxivProvider (request_delay=3.0) a hard auth/query error on every page costs 3+6=9s of pointless sleeping per page, multiplied by max_pages, before finally raising. ProviderError already exists and carries a `reason` field — the retry loop ignores it entirely. Additionally, `request_delay` (a politeness/rate-limit knob) is repurposed as the backoff base, conflating two unrelated concerns; a fast provider with request_delay=None gets 1s backoff while arXiv gets 3s for the same failure class.

---

### [SR-20260724-008] [MEDIUM] literature_review/models.py — Serde.from_dict silently drops explicit None for required fields, then crashes with an opaque TypeError; callers paper over this with the fragile '{"required": "", **data}' prefix idiom

- **Category:** Bug
- **Status:** FIXED (2026-07-24, same session)
- **Confidence:** single-reviewer
- **Suggestion:** Distinguish 'missing' from 'required'. In from_dict, if a field has no default and is absent/None, either raise a ValueError naming the field and class, or coerce to the type's zero value. Then delete the `{"candidate_id": "", ...}` splat pattern in run_stats/run_read.

orchestrator.py run_read: `ResearchBrief.from_dict({"brief_id": "", ..., **brief_data})` — if brief_data has an explicit null for a required key, from_dict skips it and `cls(**kwargs)` raises `TypeError: __init__() missing 1 required positional argument` with no hint of which artifact file was bad. The defaults-via-dict-splat idiom appears 2x in orchestrator.py and must be remembered at every future call site — the mixin leaking its limitation onto every consumer.

---

### [SR-20260724-009] [MEDIUM] literature_review/models.py — _coerce union handling picks the first non-None member arbitrarily, and uses inline __import__("types") instead of a top-level import

- **Category:** Bug
- **Status:** FIXED (2026-07-24, same session)
- **Confidence:** single-reviewer
- **Suggestion:** Import `types` at module top and use `types.UnionType`. For unions, either restrict support to Optional[X] explicitly or try each member in order and fall through on failure.

`origin in (typing.Union, __import__("types").UnionType)` — a hidden import executed on every union-typed field of every record is both slow and unidiomatic. The 'first non-None member' rule happens to work for current models (all unions are Optional[X]) but will silently mis-coerce the day someone writes `str | int`. Also `float(value)` is attempted without the bool guard that the int branch has, so a JSON `true` in a float field becomes 1.0 while in an int field it stays True — inconsistent.

---

### [SR-20260724-010] [MEDIUM] literature_review/models.py — get_type_hints(cls) and dataclasses.fields(cls) recomputed on every from_dict call — O(reflection) per record over thousands of candidates

- **Category:** Performance
- **Status:** FIXED (2026-07-24, same session)
- **Confidence:** single-reviewer
- **Suggestion:** Cache the resolved hints per class, e.g. a module-level @functools.lru_cache helper _hints(cls) or memoize on the class in __init_subclass__.

run_stats and dedupe paths call Candidate.from_dict per JSONL row. get_type_hints resolves string annotations (the module uses `from __future__ import annotations`) via eval on every call. Trivial to cache; the current shape makes deserialization the slowest part of loading large candidate sets.

---

### [SR-20260724-011] [MEDIUM] literature_review/pipeline/orchestrator.py — run_stats behavior regression: one malformed candidate row now aborts all plotting; previously bad rows were skipped per-row

- **Category:** Bug
- **Status:** FIXED (2026-07-24, same session)
- **Confidence:** single-reviewer
- **Suggestion:** Keep typed reconstruction but restore per-row tolerance: wrap Candidate.from_dict per row and skip/log bad rows, so one corrupt line in ranked JSONL doesn't kill both plots.

The old code had try/except per row. The new list comprehension sits inside the outer try, so a single row raising yields stats["plot_error"] and zero plots. Also pre-existing: stats.json is written BEFORE the plots block, so plots/plot_error keys appear only in the returned dict, never in the persisted file — file and return value silently diverge.

---

### [SR-20260724-012] [LOW] literature_review/pipeline/orchestrator.py — _load_cards typed as list[Any] and duplicate reading_dir existence checks in run_synthesize

- **Category:** Feature
- **Status:** FIXED (2026-07-24, same session)
- **Confidence:** single-reviewer
- **Suggestion:** Type the helper -> list[PaperCard] (import under TYPE_CHECKING) and drop the redundant reading_dir.exists() check in run_synthesize — _load_cards already handles it.

run_synthesize checks reading_dir.exists() then calls _load_cards which checks it again. The helper returning list[Any] throws away exactly the typing this refactor was meant to buy.

---

### [SR-20260724-013] [LOW] literature_review/review/screen.py — _validate constructs a ScreeningDecision only to immediately flatten it back to a dict

- **Category:** Feature
- **Status:** BY-DESIGN
- **Confidence:** single-reviewer
- **Suggestion:** Either return the ScreeningDecision and let the caller add artifact_version at write time, or skip the dataclass round-trip.

`decision = ScreeningDecision(...); return {"artifact_version": 1, **decision.to_dict()}` — the type exists for one line and no downstream code receives it. The only real gain is field-name drift protection, which a typed return would deliver more honestly.

---

### [SR-20260724-014] [LOW] literature_review/models.py — ResearchBrief to_dict/from_dict asymmetry: to_dict always nests constraints, from_dict accepts both layouts — two persisted shapes now exist in the wild

- **Category:** Feature
- **Status:** BY-DESIGN
- **Confidence:** single-reviewer
- **Suggestion:** Document the nested layout as canonical and consider a one-time migration note; the dual-read should not be permanent.

Also `int(2.7)` in _coerce silently truncates floats fed into int fields — acceptable but undocumented best-effort behavior.

---

### [SR-20260724-015] [LOW] literature_review/providers/arxiv.py — USER_AGENT still carries the placeholder mailto:research@example.com despite the new 'API etiquette' comment

- **Category:** Bug
- **Status:** FIXED (2026-07-24, same session)
- **Confidence:** single-reviewer
- **Suggestion:** Make the contact address configurable (env var or workspace.toml) — arXiv asks for a real contact in the UA.

The namespace typo fix and ARXIV_NS_SHORT brace normalization are correct and pinned by tests/test_arxiv_parse.py. request_delay=3.0 matches arXiv guidance.

---

### [SR-20260724-016] [INFO] tests/test_models_serde.py — Test coverage is genuinely good, but the riskiest new code (_search_with_retries) has zero test coverage

- **Category:** Feature
- **Status:** FIXED (2026-07-24, same session)
- **Confidence:** single-reviewer
- **Suggestion:** Add negative tests: explicit None on a required field, a malformed row in the run_stats plot path, and retry behavior of _search_with_retries.

The retry logic in providers/base.py — arguably the riskiest new code in the range — has zero test coverage, while the trivial request_delay >= 3.0 assertion got one. Test effort is inversely proportional to risk here.

---

### [SR-20260724-017] [MEDIUM] literature_review/providers/base.py — Retry wrapper catches bare Exception, so permanent failures (401 auth, 400 malformed query, 404) are retried 3x with exponential sleeps before ultimately failing

- **Category:** Bug
- **Status:** FIXED (2026-07-24, same session)
- **Confidence:** single-reviewer
- **Suggestion:** Discriminate transient from permanent errors — only retry on network/timeout/429/5xx, and re-raise 4xx (except 429) immediately.

_search_with_retries says 'transient errors' in its docstring but `except Exception` retries everything. A bad API key or malformed Boolean query — which will NEVER succeed — now burns base_delay*(2^attempt) seconds per page (up to ~9s for arXiv) before surfacing the same error. Slows down the exact failure cases a user most wants fast feedback on, multiplied across every page of every query. No test covers the exhaustion path or the succeeds-on-2nd-attempt path.

---

### [SR-20260724-018] [MEDIUM] literature_review/models.py — from_dict calls get_type_hints(cls) on every single invocation — expensive, uncached, and can raise NameError that aborts a whole batch load

- **Category:** Performance
- **Status:** FIXED (2026-07-24, same session)
- **Confidence:** single-reviewer
- **Suggestion:** Cache resolved hints per class and guard get_type_hints so one unresolvable annotation doesn't abort the whole load.

run_stats builds [Candidate.from_dict(...) for c in _read_jsonl(ranked_path)] — get_type_hints runs once per record. For thousands of ranked candidates this is thousands of redundant hint resolutions. Worse: if any annotation fails to resolve, get_type_hints raises and — because the stats comprehension dropped the old per-row try/except — the entire plotting step dies instead of skipping one row. Per-row fault tolerance traded for typing purity without acknowledgement.

---

### [SR-20260724-019] [LOW] literature_review/models.py — Numeric coercion silently swallows malformed values and returns the original type instead of validating or reporting

- **Category:** Bug
- **Status:** BY-DESIGN
- **Confidence:** single-reviewer
- **Suggestion:** Either coerce strictly (raise/collect errors) or log dropped/uncoerced values; don't silently leave a str in an int-typed field.

_coerce for int/float wraps conversion in try/except and returns value unchanged on failure. A stored publication_year of "2018.5" or "n.d." stays a string in a field typed int | None, and downstream code (plot_year_distribution, sorting) blows up far from the real cause, or silently mis-buckets.

---

### [SR-20260724-020] [LOW] literature_review/models.py — from_dict silently drops unknown keys and coerces null to default, masking schema drift, renamed fields, and typos in persisted JSON/TOML

- **Category:** Bug
- **Status:** BY-DESIGN
- **Confidence:** single-reviewer
- **Suggestion:** Consider a debug/strict mode that logs or collects unexpected keys so stale artifacts and field renames surface.

The mixin ignores any key not in fields(cls) and treats missing/None as apply-default. If a stored card or workspace.toml uses an old field name, the value vanishes with zero signal — the classic 'why is my data empty' bug. No test asserts behavior on unexpected/extra keys.

---

### [SR-20260724-021] [LOW] literature_review/models.py — Union coercion blindly picks the first non-None arg; ambiguous for multi-type unions and relies on types.UnionType existing (Python 3.10+)

- **Category:** Bug
- **Status:** BY-DESIGN
- **Confidence:** single-reviewer
- **Suggestion:** Handle only the Optional[X] case explicitly; for genuine multi-type unions, attempt each member or leave the value untouched.

_coerce on a Union returns _coerce(<first non-None arg>, value). Correct for int | None, but a str | int field would force everything to the first member. Also __import__("types").UnionType assumes 3.10+ with no declared floor. Currently benign, but an unguarded assumption waiting for the first multi-type union.

---

### [SR-20260724-022] [INFO] literature_review/pipeline/orchestrator.py — Inter-provider sleep between probes was removed; per-query delay now lives only inside run_probe

- **Category:** Performance
- **Status:** ACKNOWLEDGED
- **Confidence:** single-reviewer
- **Suggestion:** Confirmed acceptable — run_probe (search.py:165,195) sleeps request_delay between queries per provider, so rate-limit etiquette is preserved within each provider.

The old _time.sleep(delay*0.5) between providers in the probe loop is gone. Verified run_probe honors request_delay internally, so arXiv's 3s etiquette holds per provider. Only lost behavior is a small gap between switching providers (different hosts), which is harmless.
