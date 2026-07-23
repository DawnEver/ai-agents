# Step 01 — Research brief + concept taxonomy

Define the research scope: what to include, what to exclude, and the conceptual framework that drives query generation.

## Inputs
- `workspaces/<slug>/workspace.yaml` — active workspace

## Output

```
workspaces/<slug>/
  briefs/<brief-id>/           ← reusable brief drafts (optional)
    research_brief.yaml
  runs/<run-id>/
    research_brief.yaml        ← approved brief with SHA-256 binding
```

## Steps

1. **Derive the run ID** from the brief_id and current date (e.g. `llc-wide-voltage-2026-07-23`). Create `workspaces/<slug>/runs/<run-id>/`.

2. **Agent helps user define the research brief**. Work through these sections interactively:

   - `original_request` — the user's question in their own words
   - `research_objective` — a focused, answerable statement of what the review will establish
   - `inclusion_criteria` — what makes a paper eligible
   - `exclusion_criteria` — what disqualifies a paper
   - `constraints`:
     - `year_from`, `year_to` — when absent, propose **last 10 years** as default
     - `content_types` — when absent, propose **Journals + Conferences** as default
   - `concepts` — a taxonomy table. Each concept has:
     - `concept_id` — short machine-readable key (e.g. `edge-ai`)
     - `role` — one of: `must`, `should`, `context`, `evidence`, `exclude`
     - `term` — the primary label
     - `synonyms` — list of equivalent terms
     - `rationale` — why this concept matters to the research question
     - `source` — where the concept came from (user, literature seed, domain expert)
     - `selected` — boolean; only `selected: true` concepts feed query generation

3. **Show the concept table** in a keyword-grid format and let the user edit, add, or remove concepts. Iterate until the user is satisfied.

4. **Write** the brief to `workspaces/<slug>/runs/<run-id>/research_brief.yaml`.

5. **Validate** the brief:
   ```bash
   python scripts/lit_review.py validate-brief --brief workspaces/<slug>/runs/<run-id>/research_brief.yaml
   ```

6. **Gate — confirm the brief**:
   ```bash
   python scripts/lit_review.py confirm-brief --run-dir workspaces/<slug>/runs/<run-id> --approved-by <name>
   ```
   This computes a SHA-256 hash of the brief, writes an approval stamp, and locks the brief. Any subsequent edit invalidates the stamp.

7. Proceed to step 02 (queries).

## Resume rule

If `workspaces/<slug>/runs/<run-id>/research_brief.yaml` exists and has a valid approval stamp (`approval.approved: true` with matching `research_scope_sha256`), skip to step 02. If the brief exists but is unapproved, resume at the gate (step 6).
