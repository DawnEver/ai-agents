# Step 02 — Consensus summary

Write `ongoing/<slug>/2-review/summary.md` — the shared ground truth every downstream agent reads **before** forming opinions.

## Inputs
- `ongoing/<slug>/1-paper-text/paper.md` (entry point — abstract + section index)
- `ongoing/<slug>/1-paper-text/md/*.md`
- `ongoing/<slug>/1-paper-text/INDEX.md` (figure/table map)
- `templates/summary-template.md`

## Output
- `ongoing/<slug>/2-review/summary.md`

## Steps

1. Start with `paper.md` for title + abstract. Walk through `md/` in order.
2. Fill in every section of `templates/summary-template.md`:
   - Title & venue/year, Problem, Claimed contribution, Method, Key experiments + headline numbers, Datasets, Baselines, Limitations admitted.
3. Stay factual. **No critique here** — saved for step 04.
4. **`Obvious gaps`** section (last). List only objectively observable absences — not judgements. Examples:
   - "No code or data release URL in the paper."
   - "Single-seed runs across all reported numbers; no variance reported."
   - "No ablation isolating the contribution claimed in §1 bullet 2."
   - "Figure 4 caption claims robustness but no robustness benchmark is reported."
   Keep to bullets, 5–10 max. These are facts, not opinions. Downstream reviewers may pick them up and run.
5. Ensure `2-review/` directory exists, write to `ongoing/<slug>/2-review/summary.md`.
6. Show the summary to the user and confirm it matches their reading before moving to step 03.

## Hard rule

If you cannot fill in a non-gap section from the PDF, write `Not stated in paper.` — never fabricate. For `Obvious gaps`, "none observed" is a valid answer if the paper really is thorough.
