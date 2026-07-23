# Query Planning Guide

Guide for the agent when generating search queries from an approved research brief.

## Principles

1. **Derive from selected concepts only**: Only concepts with `selected: true` participate in query generation.
2. **Role-driven logic**: `must` concepts are AND-ed; `should` are OR-ed within groups; `exclude` are NOT-ed.
3. **Synonyms expand recall**: Every concept's synonyms are OR-grouped with the canonical term.
4. **One query per concept combination**: If the brief has 2 must concepts and 3 should concepts, generate queries that systematically combine them.
5. **Provider-aware syntax**: IEEE uses `"..."` for phrases and Boolean operators. arXiv uses `search_query` field syntax. Semantic Scholar uses a different syntax.

## Query Structure

Each query in `queries.yaml`:
```yaml
queries:
  - query_id: "Q1"
    purpose: "Core LLC + wide voltage papers"
    provider: ieee_xplore            # Which provider adapter to use
    expression: '("LLC resonant converter" OR "LLC converter") AND ("wide voltage range" OR "wide gain range")'
    year_from: 2018
    year_to: 2026
    content_types: [Journals, Conferences]
    sort: relevance                   # relevance | newest
    enabled: true
    concept_ids: ["c01", "c02"]       # Which concepts this query covers
    provenance: "Generated from c01(must) AND c02(must)"
```

## IEEE Xplore Syntax

- Boolean: `AND`, `OR`, `NOT` (uppercase)
- Phrases: `"exact phrase"` (double quotes)
- Wildcards: `*` (e.g. `convert*` matches converter, converters, conversion)
- NEAR operator: `NEAR/n` (within n words)
- Precedence: parentheses `()`

## Query Evaluation Heuristics

After probing (page 1 result):
- **Too many results** (>500): Add more specific MUST concepts, narrow year range, or restrict to Journals only.
- **Too few results** (<20): Broaden synonyms, add CONTEXT concepts, expand year range, include Conferences.
- **Good range**: 20–500 → proceed to full search.

## Provider-Specific Notes

### IEEE Xplore
- Search field: "All Metadata" by default
- Refinements: `ContentType:Journals`, `ContentType:Conferences`
- Ranges: `{year_from}_{year_to}_Year`
- Maximum: 5 pages × 25 results = 125 per query

### arXiv (Phase 4)
- API: `http://export.arxiv.org/api/query`
- Search prefix: `all:`, `ti:`, `au:`, `abs:`
- Boolean: `AND`, `OR`, `ANDNOT`

### Semantic Scholar (Phase 4)
- API: `https://api.semanticscholar.org/graph/v1/paper/search`
- Query parameters: `query`, `year`, `fieldsOfStudy`, `limit`, `offset`
