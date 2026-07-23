---
name: second-round-proof-review-handling
created: 2026-06-24
accessed: 2026-06-24
access_count: 1
tier: short
---

# Second-round (R1) proof review — handling pattern

First real run of the pipeline on a **journal proof bundle** (TII-26-0916.R1), not a clean
single manuscript. Key learnings:

## Ingest behaviour on "Files for peer review" bundles
- A proof PDF = revised manuscript **+** point-by-point response letter in one file.
- `scripts.ingest` multi-paper detection splits the **response letter into
  `1-paper-text/appended/`** (it looks like a second paper). Reviewer #1/#2/#3 + Associate
  Editor comments and the author replies land there. Always read the `appended/` block to
  separate author rebuttal from manuscript text.
- The `****` markers in the appended md files delimit author-reply blocks from quoted
  reviewer comments.

## Tone-gate from user
- User flagged the paper as 友军 (friendly) → "更多注意格式问题，不要太尖锐".
- Recorded as `tone: friendly` in `review-config.md`. Drove a **format/presentation-focused**
  review and a deliberate skip of the adversarial 4-angle fanout.
- Output register: credit the rebuttal explicitly, list resolved concerns, then only
  editorial points. Recommendation calibrated to **Minor Revision**.

## Fidelity guard that mattered
- Ingest OCR garbled Table II and merged words ("highresolution"). **Cross-checked page
  images** (`img/sec03/page-10-table-ii.png`) before flagging — Table II renders cleanly in
  the actual proof, so extraction artifacts were NOT reported as paper defects.

## Real catches (defensible)
- pp-vs-% units: segmentation gains written as "%" are absolute percentage-point deltas of
  Table V. (→ new `presentation-consistency` angle added to global library.)
- "are-based" → "area-based" typo; mixed Fig./Figure; Fig. 9 still dense.

## Archive friction (Windows/OneDrive)
- `mv` / `Move-Item` failed with "in use" (OneDrive sync + editor lock on the 23 MB PDF).
- **robocopy /MOVE /R:2 /W:1** succeeded file-by-file (exit code 1 = files copied OK).
- The empty source dir shell may stay process-locked; leave it for manual deletion.
