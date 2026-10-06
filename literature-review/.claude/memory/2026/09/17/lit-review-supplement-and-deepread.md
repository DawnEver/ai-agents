---
name: lit-review-supplement-and-deepread-2026-09-17
description: "Extending a review after the corpus is built — probe is the safe gap-filling path (search would invalidate imported screening), a probe is a pointer set not a survey, and the concept taxonomy bounds recall"
metadata:
  type: engineering
---

# Extending a review after the corpus is built

`created: 2026-09-17, accessed: 2026-09-17`

How to answer a question that arrives *after* search and screening are done, without
rebuilding the corpus or silently over-claiming recall.

## 1. Use `probe`, never `search`, for a mid-review round

| command | writes | safe mid-review? |
|---|---|---|
| `lit-review search --topic <slug>` | regenerates `search/`, `screening/packets/`, `candidates_ranked.jsonl` | **No** — new packets invalidate every already-imported screening result |
| `lit-review probe --queries <file> --out <dir> --provider <p>` | only under `--out` | **Yes** — `candidates_ranked.jsonl`, `screening/`, and imported results are untouched |

`probe` takes explicit paths for both input and output, so it is fully decoupled from the
workspace state. Author a separate `queries_supplement.toml` at the workspace root
(same `[[queries]]` shape as `queries.toml`) and point `--out` at
`search/probe/<round>/`. The round is then a first-class artifact with its own audit log
and raw payloads, and the original corpus is provably unchanged.

Re-running the full `search` is still the correct move when recall genuinely matters —
it is just a different, much more expensive decision, because it re-opens screening.

## 2. A probe is a pointer set, not a survey

`probe` fetches **one page of ~5 results per query** and has no `--max-pages`. It reports
a `total` count that is the provider's estimate for the whole query, not what it fetched.
So:

- A "0 hits" or "2 hits" from a probe is a real signal about that query's discriminating
  power, but
- the 5 titles returned are a citation-dominated sample, and
- recall is far below a real search round.

Any conclusion drawn from probe output must be scoped as *"not found in this pointer
set"*. Pair it with the local re-filter (see `lit-review-search-provider-quirks` §4) —
re-ranking harvested candidates offline is free and does not consume provider quota.

## 3. The concept taxonomy is a recall ceiling, and it is invisible later

Queries are authored from the brief's concept taxonomy. A question that arrives mid-review
and maps to **no** concept therefore cannot have been covered by the original round — not
because the literature is thin, but because nothing asked.

Practical consequences:

- When a new question maps to no existing concept, treat that *absence* as the trigger to
  author a supplementary round. Do not read corpus silence as literature silence.
- Write the finding as **"not found in this corpus"**, never "no such work exists". The
  difference survives review; the second does not.
- Measured example from this session: a mid-session objection decomposed into four
  checkable claims. Two mapped onto existing concepts and were well covered; two did not,
  and those two were exactly where the corpus was thinnest (one had a single candidate).
  The gap tracked the taxonomy, not the field.

## 4. Parallel deep-read of PDFs via pre-extracted text

The pipeline's `ingest` step may never have run, but PDF text extraction does not need it —
PyMuPDF (`fitz`) was already present in the ambient Python. Extract every PDF once, up
front:

```python
import fitz, glob, os
for p in sorted(glob.glob('pdfs/*.pdf')):
    txt = '\n'.join(pg.get_text() for pg in fitz.open(p))
    open('notes/text/' + os.path.basename(p).replace('.pdf', '.txt'), 'w', encoding='utf-8').write(txt)
```

Why this ordering matters: N subagents can then each `Read` plain text in parallel instead
of every one of them parsing PDFs. It also keeps the extraction out of every agent's
context budget, and makes grep-based checks across the whole set cheap afterwards.

These text dumps are scratch, not deliverables — clean them or keep them deliberately, but
do not let them masquerade as ingests.

## 5. The deep-read prompt that produced usable evidence

What worked, when several agents each covered a disjoint set of papers:

- A **fixed field template per paper** (citation, geometry, method, numbers, stated costs,
  quotables), identical across agents so the reports are directly comparable.
- A **named list of the specific claims being tested**, so agents look for disconfirming as
  well as confirming text.
- An explicit **"say `not stated` when the paper does not say"** instruction, and an
  instruction to **quote verbatim rather than paraphrase**.

That last pair is what made the output falsifiable. Agents returned honest negatives
("none of these papers contains the words …", "this paper cannot be cited either way on
…"), which is exactly the material that turns a summary into an argument with a known
boundary. Without the instruction, the same agents would have written confident paraphrase
covering the same gaps.

## Files

- `lit-review probe --help` / `lit-review search --help` — the decoupling is visible in the flags
- `notes/text/` — pre-extracted PDF text (scratch)
- `queries_supplement*.toml` at the workspace root — supplementary rounds
