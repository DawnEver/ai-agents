# Step 02b — Literature context & author background

Search for the most relevant prior work and profile the authors. Extract key references from the paper itself, search IEEE Xplore for additional context, and look up the authors' research track record. Write a shared landscape summary that all downstream agents read.

## Inputs
- `ongoing/<slug>/2-review/summary.md` — consensus (especially `Obvious gaps` and key claims)
- `ongoing/<slug>/1-paper-text/paper.md` — full paper text (references section + author list)
- `ongoing/<slug>/2-review/angles.md` — optional `literature_n:` override (default N = 5)

## Output
- `ongoing/<slug>/2-review/literature.md`

## Steps

### 1. Read N
Check `ongoing/<slug>/2-review/angles.md` for a line `literature_n: <N>`. If absent or file doesn't exist yet, use N = 5.

### 2. Extract references from paper (Source A)

Read `summary.md` and `1-paper-text/paper.md`. Identify up to 15 candidate references using these priority signals (in order):
1. Cited in the summary's key claims or contribution bullets
2. Cited in the `Obvious gaps` section of `summary.md`
3. Appears in the paper's related-work or introduction sections
4. Exclude self-citations (same authors as the paper)

For each candidate extract: **title**, **authors**, **year**, **venue** (if visible in the references list).

### 3. Search IEEE Xplore (Source B)

Build 2–3 search queries from:
- Top 4 content nouns from the paper title
- Method name (if identifiable from summary)
- Task/domain keywords from summary

Run `WebSearch` for each query:
```
site:ieeexplore.ieee.org <keywords> 2022 2023 2024 2025
```

Pick top 2–3 unique results **not already in Source A** (check by title similarity). Prefer papers ≤3 years old. For each result, record: title, authors, year, venue, and a one-sentence relevance note.

If WebSearch returns no usable results, proceed with Source A only and note "IEEE search: no results" in the output.

### 4. Deduplicate and rank

Merge Source A + Source B. Drop duplicates by title similarity (strip function words, compare key nouns). Keep the top N entries ranked by relevance to the paper's core claims.

### 5. Author background

Extract the full author list from `1-paper-text/paper.md` (usually in the header or first page). For each **corresponding author** (marked with `*` or listed with email), and for the **first author**, search:

```
WebSearch: "<First Last>" site:scholar.google.com OR site:researchgate.net OR site:ieee.org
WebSearch: "<First Last>" "<institution>" research papers
```

Collect for each searched author:
- **Affiliation** (institution, lab/group if visible)
- **Research focus** (2–3 keywords from their profile or prior paper titles)
- **Prior work in this area**: up to 3 most relevant prior papers by this author (title, year, venue) — especially work that predates or directly relates to this submission
- **h-index or citation count** if easily visible (optional; skip if not on surface)

**Key question to answer**: Does this paper represent a natural evolution of the authors' prior work, or is it a new direction? Are they established authorities in this sub-field or newcomers?

If no profile is found for an author after 2 search attempts, record "profile not found" and move on.

### 6. Write `literature.md`

```markdown
## Literature Context

### Paper Positioning
<2–3 sentences: where this paper sits in the landscape — dominant approach it extends, closest prior systems, what makes its problem setting distinct>

### Key References (from paper)
1. **[Title]** — [Authors, Year, Venue] — [1-sentence note: what it contributes and why it matters here]
...

### Related Work (IEEE search)
1. **[Title]** — [Authors, Year, Venue] — [1-sentence note: how it relates to this paper]
...
*(If no IEEE results found: "IEEE search returned no usable results for this query.")*

### Author Background

#### [First Author Name] (first author)
- Affiliation: [institution / lab]
- Research focus: [keywords]
- Relevant prior work:
  1. [Title, Year, Venue]
  2. ...
- Track record note: <1 sentence — e.g. "3 prior papers on X; this submission extends their ICLR 2023 work.">

#### [Corresponding Author Name] (corresponding, if different)
- ...
*(Repeat for each searched author. List remaining authors by name only if not searched.)*

### Research Landscape Summary
<3–5 sentences: current state of the field, dominant approaches, open problems that this paper's venue/reviewers would care about>
```

## Hard rules

- Write exactly what you found — no invented titles, authors, or affiliations.
- If a reference or profile is incomplete, include what's available; do not fabricate the rest.
- Proceed gracefully with fewer than N papers or missing author profiles rather than failing.
- Do not form opinions or critique here — this is a factual context file. Critique happens in step 04.
- Author background is context for reviewers, not grounds for bias. Record facts, not judgements about credibility.

## Resume

If `ongoing/<slug>/2-review/literature.md` is non-empty, skip this step entirely.
