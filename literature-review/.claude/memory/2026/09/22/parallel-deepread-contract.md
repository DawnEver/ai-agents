---
name: parallel-deepread-contract-2026-09-22
description: Sixteen papers across four parallel readers — the output template is what made the cards comparable, and three cross-paper checks caught what no single card could
metadata:
  type: engineering
---

# A parallel deep-read needs a written contract, and the cross-checks earn their keep

`created: 2026-09-22, accessed: 2026-09-22`

## What made it work

Sixteen full texts, four readers in parallel, four papers each. Two artefacts
were supplied to every reader and are the reason the output is usable:

1. **One explicit output template**, fixed in advance: citation; problem; method
   *reconstructed from the formulation* (design variables, objective,
   **constraint list**, physics in the loop, parameterisation, optimiser); every
   number with the operating point it was obtained at; the figures carrying the
   argument; verification; stated limitations and unstated ones kept apart; what
   is reusable; per-question verdicts; open questions.
2. **A scoring lens** with named coordinates, each carrying **signals** and
   **anti-signals** — so a reader could mark a paper as *not* exhibiting a
   property, rather than having to invent a scale.

Two instructions did most of the work in practice:

- **"Write `not given` where the paper does not say — never fill a gap by
  inference."** A missing statement is itself a finding; an inferred one
  destroys cross-paper comparability, which is the entire point of the format.
- **"Quote, do not paraphrase, for anything load-bearing."** Especially the
  constraint list and any claim of simultaneity or coupling. Every later
  cross-check in this run rested on having the verbatim sentence available.

Because every card had the same headings, sections could be pulled and compared
across papers mechanically — which is what made the checks below possible at all.

## The three cross-paper checks, none visible from a single card

**1. Same-group detection.** Several papers that looked like independent results
were one research programme: shared authors, a shared machine cross-section, and
in one case a formulation where paper A's equation *is* paper B's equation. Two
of them shared a group **and did not cite each other**, while the later one
deferred to future work the very thing the earlier one had already done. A set
of papers from one group is not N independent confirmations — and the count that
matters for a state-of-the-art claim is programmes, not papers.

**2. Post-processing that defeats the stated constraint.** A paper imposed
manufacturability constraints the optimiser did not enforce, then smoothed the
result **by hand** before building it, with the performance cost of that step
unreported. A different paper made exactly this its novelty claim. Where a
constraint is applied outside the loop, the optimised result is not the design
that was evaluated.

**3. A reference that does not resolve to what the text says it is.** A paper
called a reference "our previous work" three times; as printed, that reference
belongs to a different group. Either a numbering error or a misattribution —
and either way the consequence is the same and worth stating: **the derivation
the paper depends on is not in that paper.** Checking that a load-bearing
citation actually resolves is cheap and occasionally decisive.

## Also worth carrying

- **Equation fragments degrade in PDF text extraction.** Readers should mark an
  equation as *not reliably recoverable* rather than reconstructing it.
  Reconstructing would put invented mathematics into a document that will be
  quoted from.
- **Baseline discipline is the fastest quality signal.** For each headline
  number, require metric + baseline + operating point. In this batch most papers
  supplied fewer than three, and the ones that supplied all three were
  immediately distinguishable. A percentage missing any of the three is
  undefined, not approximate.
- **Give the resolved absolute path of every shared input in the prompt.** A
  reader told "the lens lives at `lenses/<name>.toml`" looked inside the working
  directory; the file was one level up, outside it. The reader noticed and said
  so, which is the only reason it cost nothing.
