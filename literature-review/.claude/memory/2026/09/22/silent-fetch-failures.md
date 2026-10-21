---
name: silent-fetch-failures-2026-09-22
description: A fetch that could not happen must never be recorded as a fetch that found nothing — four instances of this class found and fixed in cc-academia in one day
metadata:
  type: engineering
---

# "Could not fetch" must never be recorded as "found nothing"

`created: 2026-09-22, accessed: 2026-09-22`

Four separate defects in cc-academia, all the same shape: the pipeline reported a
failure as an empty result. In a literature review that misreading is the most
expensive one available — "no such work exists" is exactly the conclusion a
prior-art search must never reach by accident.

## The instances

**1. A probe that failed was labelled `success`.** `PaperSource.probe`
*deliberately* returns a source failure as a value — `Probe(total_count=0,
failure_reason="http_429")` — rather than raising, and a test pins that
behaviour ("a dead source is an answer, not a crash"). But `run_probe` then
wrote `"status": "success"` as a hard-coded literal that no data could
contradict. The tell was a summary row carrying `failure_reason=http_429`
directly beside `status=success`. Both statements came from the same dict; only
one of them was derived from the probe.

**2. A documented `.env` that was never read.** The workspace README says API
keys live in a `.env` at a named path. Nothing on the search path loaded it —
only two unrelated helpers did, and they looked under the plugin root, which in
an installed plugin holds no `.env` at all. Symptom: an operator sets a key in
the documented place and the API answers "missing key".

**3. Declared constraints that never reached the provider.** The brief's
`[constraints]` table carried a year range for every query in every review.
The forwarding function read those keys from the *query* dict only, so the
brief's values were never applied. Every date bound ever written into a brief
was decoration, and no output said so.

**4. A default pointing at a dead endpoint.** The workspace-initialisation
command wrote a provider name whose search endpoint ignores its own payload and
answers with front matter. A freshly created workspace therefore defaulted to a
source that cannot work, yielding zero candidates for reasons unrelated to the
literature.

## The general rules

- **When a source reports failure as a *value*, derive the verdict from that
  value — never from having reached the next line.** "No exception was raised"
  is not "the source answered". The code path is not evidence.
- **A config file that is documented but never read is worse than one that is
  absent.** The operator believes it is configured and finds out otherwise at
  the API boundary, far from the cause.
- **A filtering or defaulting decision must be visible in the artifact.** The
  fix for instance 1 writes the reason and the HTTP status into all three
  outputs, and a later filter records its rule and its threshold per row. A
  silent drop and an empty result are indistinguishable downstream.

## What the fix looks like

- Give the failure a machine-readable carrier (`failure_status: int | None`) so
  callers can branch without parsing prose, and add an `is_account_failure`
  predicate for "this will repeat for every remaining item".
- Distinguish *transient* ("would a retry help?" — yes for a rate limit) from
  *account* ("will this repeat for every remaining query?" — also yes). The two
  questions have the same answer for a 429 and demand opposite behaviour.
- On an account failure, stop the run and record the untouched items as
  `not_probed` with the reason, rather than repeating a wall once per item.
- Read the reason back from the artifact (`failure_reasons()`) so it outlives
  the process that discovered it; an exception object dies with the run.

## Verified by

`tests/litreview/test_probe_artifacts.py` — every artifact must agree on a
query's verdict; a failure carries its reason in all of them; an account failure
aborts without re-probing; a query-level failure does not abort.

## Files

- `src/academia/sources/base.py` — `Probe.failure_status`, `is_account_failure`
- `src/academia/core/http.py` — `ACCOUNT_STATUSES`, `error_status()`
- `src/academia/litreview/search.py` — `run_probe`, `run_search`,
  `failure_reasons()`, `_query_defaults`, `_query_kwargs`
- `src/academia/cli/dispatch.py`, `src/academia/core/paths.py` — `.env` loading
