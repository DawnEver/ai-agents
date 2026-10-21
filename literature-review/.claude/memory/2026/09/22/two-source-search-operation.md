---
name: two-source-search-operation-2026-09-22
description: Two search sources are near-disjoint rather than redundant, and the screening importer requires a decision for every candidate in the ranked file
metadata:
  type: engineering
---

# Two-source search, and the importer's full-coverage requirement

`created: 2026-09-22, accessed: 2026-09-22`

Two operational facts about the literature-review search that change how a run
has to be assembled.

## The two sources are near-disjoint, not redundant

An API-based scholarly index and a browser-driven publisher search, run over the
same topic with per-provider query sets, produced candidate sets that overlapped
on roughly **2.7%** of records. The second source is therefore not a supplement
to the first — it is a required half. A review run on the API provider alone
would have missed the majority of one literature type while looking complete.

The reason is coverage: the API indexes that publisher's *journals* well and its
*conference* proceedings poorly, and in this field the conference record is where
the method work concentrates.

Consequence for planning: budget for both from the start, and do not treat the
second source as a nice-to-have to add if results look thin. Thin results from
one source are not evidence that the field is thin.

## The importer requires a decision for EVERY candidate

The screening importer reads the ranked candidate file and raises if any
candidate lacks a decision — it validates *coverage of the universe*, not just
the shape of the rows it is given. So a local pre-filter that shrinks the
candidate set before screening breaks the import, even though the filter is
doing something sensible.

Two ways to reconcile this, and the honest one is not obvious:

- **Do not quietly shrink the universe.** Instead, emit explicit rows for what
  the filter dropped, carrying the filter's rule and reason per row, so the
  final artifact contains the full decision set and nothing disappears. A
  filter that drops most of the candidates must be auditable, because the
  result is judged by what it failed to find.
- The dropped rows should be labelled as a *filter decision, not a screening
  judgment* — otherwise the aggregate counts read as though a screener rejected
  them, which overstates how much was actually examined.

## Filtering the ranking is mandatory, not optional

The API's ranking score weights citation count far above how many queries a
record matched, so the head of the ranked list is whatever is most cited and
contains any query term. Measured on one run, the top of the list was unrelated
highly-cited work from other fields entirely.

The ranking is not a filter and must not be used as one. Re-score locally on
concept anchors drawn from the brief instead: cheap, no API calls, and
re-runnable at a different threshold without re-searching.

One refinement worth copying: when the rule requires a method term, give it an
escape branch for the deliberately-in-scope boundary class — the papers that use
a *different* geometry method and would be lost by a method-specific anchor.
Measured: a small number of records, and they were exactly the class the scope
statement said must be compared against.

## Files

- `tools/domain_filter.py` — the local anchor filter (per-row scores and reasons
  retained in `search/domain_dropped.jsonl`)
- `tools/ieee_search.py` — the browser-driven publisher search
- `src/academia/litreview/screen.py` — `import_agent_screening`, `_validate`
