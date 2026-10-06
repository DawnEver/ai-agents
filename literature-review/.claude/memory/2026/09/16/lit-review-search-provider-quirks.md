---
name: lit-review-search-provider-quirks-2026-09-16
description: Search providers disagree on query length syntax and ranking — per-provider query sets, OpenAlex credit quota, and why its ranking cannot be trusted for recall
metadata:
  type: engineering
---

# Search-provider quirks that break naive query sets

`created: 2026-09-16, accessed: 2026-09-16`

## Query length must be tuned per provider

The same expression cannot serve more than one provider.

- **OpenAlex / IEEE / DBLP all strip Boolean operators, quotes and parentheses
  before sending** (`openalex.py:317`, `ieee.py:118`, `dblp.py:77`). The
  expression is a bag of terms and the endpoint's own relevance does the work.
  Writing `"A" AND (B OR C)` achieves nothing except littering the request.
- **OpenAlex** flattens to a bag of words and ranks by relevance — more terms
  add context and generally help.
- **IEEE `queryText` matches strictly.** Measured on a 27-query set: 10
  expressions of 7–8 terms returned literally `total=0`, and each one dropped
  below ~5 terms started returning hits. An 8-term expression scoring 0 went to
  5 hits once trimmed to 3 terms. (Concrete query strings are deliberately not
  reproduced here — they would leak the research topic into project memory.)

Practical consequence: **keep one query set per provider**, short (2–4 terms)
for IEEE, longer for OpenAlex. A single `queries.toml` will silently under-fetch
on one of them and look like "the literature is thin" rather than "the query is
too long".

## OpenAlex free tier is credit-based, not request-based

```
X-RateLimit-Limit: 1000
X-RateLimit-Credits-Required: 10
X-RateLimit-Remaining: 0
Retry-After: 36588          # ~10 hours
```

So ~**100 requests/day**, not 100k. One 27-query probe plus two searches
exhausted it and every subsequent call 429'd. Budget accordingly: probe with a
handful of queries, not the whole set.

`ACADEMIA_CONTACT` does not help once the quota is spent — it only raises the
rate limit for the polite pool while quota remains.

## OpenAlex ranking is citation-dominated — do not trust it for recall

`candidates_ranked.csv` carries the reasoning inline:

```
query_matches=1; citation_count=13693; publication_year=2013
```

A paper matching **one** generic term outranked everything relevant by virtue of
13k citations. With bag-of-words queries this floods the top of the list with
unrelated mega-cited work (a clinical guideline topped one machine-design
query set). Generic terms are the trigger: `model`, `design`, `optimization`,
`motor` (which also means motor control / motor behaviour in neuroscience),
`reduction`.

**Mitigation that worked:** do not trust the ranking. Re-filter the harvested
candidates locally on domain-anchor terms (2+ matches against a curated
vocabulary) — this recovered 589 relevant papers from 1362 candidates with no
API calls, which also matters when the quota is gone. Re-ranking locally is
cheap; re-searching is not.

## Corollary

Every query should carry at least one term that is unambiguous within the
domain. A query made entirely of generic words is unrankable no matter how many
results it returns.

## Files

- `src/academia/sources/{openalex,ieee,dblp}.py` — `adapt_expression` overrides
- `src/academia/litreview/search.py` — query execution, dedupe, ranking
