# Step 03 — Search and abstract screening

Execute queries against configured providers, deduplicate results, and screen abstracts via agent delegation.

## Inputs
- `workspaces/<slug>/runs/<run-id>/queries.yaml` — approved query plan

## Output

```
workspaces/<slug>/runs/<run-id>/
  search/
    queries/
      <query-id>/
        raw/                     ← raw provider responses
        candidates_raw.jsonl     ← per-query normalised candidates
        candidates_raw.csv       ← human-readable candidate summary
    candidates_ranked.jsonl      ← merged, deduplicated candidate records
  screening/
    screening_stage1.jsonl       ← screened candidates with agent decisions
    screening_packet.jsonl       ← packet sent to abstract screener
    screening_packet.csv         ← human-readable packet summary
```

## Steps

1. **Probe** each query against its provider to estimate result counts:
   ```bash
   python scripts/lit_review.py probe --queries workspaces/<slug>/runs/<run-id>/queries.yaml --out workspaces/<slug>/runs/<run-id>/search/probe/
   ```
   This returns estimated hit counts per query without downloading full results. Useful for detecting over-broad or over-narrow queries before committing to a full search.

2. **Evaluate** probe results and adjust queries if needed:
   ```bash
   python scripts/lit_review.py evaluate-queries --queries workspaces/<slug>/runs/<run-id>/queries.yaml --probe-results workspaces/<slug>/runs/<run-id>/search/probe/ --out workspaces/<slug>/runs/<run-id>/search/evaluation/
   ```
   Flag queries with zero results or excessive hits (> 500). Let the user adjust and re-probe. If queries change, return to step 02 gate for re-confirmation.

3. **Search** — execute the final queries:
   ```bash
   python scripts/lit_review.py search --queries workspaces/<slug>/runs/<run-id>/queries.yaml --out workspaces/<slug>/runs/<run-id>/search/ --evaluation workspaces/<slug>/runs/<run-id>/search/evaluation/
   ```
   The query defines its provider; the search dispatcher routes accordingly. Currently IEEE is the primary provider. Raw responses are saved per query for audit.

4. **Normalise** per-query results into a common schema:
   ```bash
   python scripts/lit_review.py normalize-candidates --raw workspaces/<slug>/runs/<run-id>/search/queries/<query-id>/raw/response.json --query-id <query-id> --out workspaces/<slug>/runs/<run-id>/search/queries/<query-id>/
   ```
   Repeat for each raw query response page.

5. **Deduplicate and rank** across all normalised candidates:
   ```bash
   python scripts/lit_review.py dedupe-rank --input workspaces/<slug>/runs/<run-id>/search/queries/<query-id>/candidates_raw.jsonl --out workspaces/<slug>/runs/<run-id>/search/
   ```
   Repeat for each query, then merge results. Deduplication uses DOI, title normalisation, and author-year fingerprinting. Ranking orders by relevance score (where available) or recency. Output: `candidates_ranked.jsonl`.

6. **Make screening packets** — create the screening packet (agent batches manually from this):
   ```bash
   python scripts/lit_review.py make-screening-packet --candidates workspaces/<slug>/runs/<run-id>/search/records.jsonl --out workspaces/<slug>/runs/<run-id>/screening/
   ```
   The agent then splits the output into batches of 10–20 candidates when sending to the abstract screener.

7. **Agent screen** — for each batch, delegate to the `literature-abstract-screener` agent. The agent reads each candidate's title and abstract, applies inclusion/exclusion criteria from the brief, and returns a decision (include/exclude/uncertain) with a brief rationale. Collect the JSONL output for each batch.

8. **Validate completeness** — ensure every candidate in every batch received a decision. Re-run any incomplete batches.

9. **Import screening results**:
   ```bash
   python scripts/lit_review.py import-agent-screening --candidates workspaces/<slug>/runs/<run-id>/search/records.jsonl --batch workspaces/<slug>/runs/<run-id>/screening/batches/batch_001_results.jsonl ... --out workspaces/<slug>/runs/<run-id>/screening/screening_stage1.jsonl
   ```

10. Report screening statistics (total candidates, included, excluded, uncertain) and proceed to step 04 (acquire).

## Resume rule

| Existing artifact | Action |
|-------------------|--------|
| `screening/screening_stage1.jsonl` | Skip to step 04 |
| `search/records.jsonl` | Skip to step 6 (make screening packets) |
| `search/queries/<id>/normalized.jsonl` (partial) | Resume normalisation for missing queries, then step 5 |
| `search/queries/<id>/raw/` (partial) | Resume search for missing queries, then step 4 |
| `queries.yaml` (approved) | Start from step 1 (probe) |
