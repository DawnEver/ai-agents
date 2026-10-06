---
name: headline-numbers-need-a-denominator-2026-09-20
description: a reported percentage is undefined until you know the metric, the baseline and the operating point — and a table can state the opposite of the sentence describing it
metadata:
  type: engineering
---

# "Up to N% better" is not a claim until you name the metric

Every headline percentage needs three things before it means anything: **which
quantity**, **against what baseline**, **at which operating point**. Papers
routinely supply fewer than three. Restate each headline as those three terms;
if one is missing, treat the claim as undefined rather than approximate.

## Forms this took, all in one reading session

- **The metric was a ratio of two quantities, not either quantity.** A claimed
  reduction turned out to be the reduction of a *ratio* between two losses. The
  same operating point showed a far smaller reduction in absolute total loss —
  and on the ratio's own terms the comparison was flattering. Two papers quoting
  the same headline can be quoting incompatible metrics.
- **"Independent of X" was contradicted by the paper's own results table.** One
  subgroup was double the other; the sentence generalising over both was written
  anyway.
- **An improvement quoted on averages, where the maximum got worse.** The
  quantity that governs the engineering limit (the peak, not the mean) had
  degraded, and the paper led with the mean.
- **A comparison that was not like-for-like.** A large advantage was quoted
  between two designs running at different currents, normalised on a
  "utilisation" product rather than at constant output. The paper gave the
  constant-output case elsewhere; the headline used the flattering one.
- **A limit asserted but never defined.** "Enables operation above *N* units"
  with no statement anywhere of what the limit is.

## The habit

For each headline: metric + baseline + operating point. Then check the *figure
or table* against the *sentence describing it* — they disagree more often than
one expects, and the table is the evidence. Where the definition exists only in
the plotting data, recovering it (see the figure-data technique) is usually the
only way to state what the paper actually claims.

## Reporting

When a claim turns out to be metric-dependent, **say which metric you are
using** in anything you write downstream, or the comparison will not survive
being checked.
