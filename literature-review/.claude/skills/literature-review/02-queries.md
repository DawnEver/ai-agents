# Step 02 — Query planning

Generate Boolean search queries from the approved brief's selected concepts. Each query binds to the brief via SHA-256 so the chain of provenance is preserved.

## Inputs
- `workspaces/<slug>/briefs/<brief-id>/research_brief.yaml` — approved and locked brief

## Output

```
workspaces/<slug>/runs/<run-id>/
  queries.yaml            ← approved query plan with SHA-256 binding to brief
```

## Steps

1. **Read the approved brief**. Extract all concepts with `selected: true` and `role` in `[must, should, context]`.

2. **Generate Boolean queries** from the concept taxonomy:
   - `must` concepts → AND terms (required)
   - `should` concepts → OR groups within an AND block (preferred but not strict)
   - `context` concepts → OR terms added to broaden recall
   - Each query specifies:
     - `purpose` — what this query targets in the literature
     - `scope` — which part of the research question it addresses
     - `expression` — the Boolean string
     - `limits` — year range, content type constraints from the brief

3. **Present the query plan** to the user. Show each query's purpose, Boolean expression, and scope. Let the user edit, reorder, add, or remove queries.

4. **Write** the query plan to `workspaces/<slug>/runs/<run-id>/queries.yaml`.

5. **Gate — confirm the query plan**:
   ```bash
   python scripts/lit_review.py confirm-queries --run-dir workspaces/<slug>/runs/<run-id> --approved-by <name>
   ```
   This computes a SHA-256 hash binding the queries to the approved brief. Any edit to either the brief or the queries invalidates this stamp.

6. **If the user edits a query after confirmation**, the approval stamp is invalidated. Return to step 5 (re-confirm). Never proceed to step 03 with an unapproved or invalidated query plan.

7. Proceed to step 03 (search and screen).

## Resume rule

Check `workspaces/<slug>/runs/<run-id>/queries.yaml`. If it exists and its `approval.approved` field is `true` with a matching `queries_sha256`, skip to step 03. If unapproved or invalidated, resume at the gate (step 5).
