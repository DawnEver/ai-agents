---
name: data-that-exists-only-in-a-figure-2026-09-20
description: plotted-but-never-tabulated values can be recovered from PDF vector data, and a figure can be internally inconsistent — the caveats that come with both
metadata:
  type: engineering
---

# Values that live only in the plot

Papers frequently state a headline number and never define it, while the data
behind it sits in a figure and nowhere else — no table, no appendix. **PDF
vector data can be parsed to recover the plotted points**, which is what made
several cross-checks possible: reconstructing a curve from its path coordinates
is enough to identify which metric a headline percentage refers to, and to
compute the same quantity under a different definition.

Two results from doing this are worth expecting:

- The reconstruction resolved a claim the text left undefined — it identified
  the *ratio* being quoted, and showed how much smaller the effect was on an
  absolute basis.
- It exposed a **caption/axis mismatch**: a figure captioned in relative terms
  plotted absolute values on an axis labelled with absolute units.

## Caveats

- **Label reconstructed values as reconstructed.** They are read off geometry,
  not quoted from the paper, and the distinction matters to anyone reusing them.
- **A figure can be internally inconsistent with itself.** A printed dimension
  in a cross-section drawing did not match the geometry actually drawn in that
  figure at that figure's own scale — off by roughly a factor of 1.7. Any claim
  resting on that dimension is therefore undefined, and the text's other
  numerical consistency checks (an area ratio, say) can be used to work out
  which reading is self-consistent.
- Rescale using the figure's *own* printed dimensions rather than assuming a
  scale, or the reconstruction inherits the error you are trying to find.
