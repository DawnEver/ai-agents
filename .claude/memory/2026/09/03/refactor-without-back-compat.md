---
name: refactor-without-back-compat
description: "The user asks for first-principles refactors with no backward compatibility; deleting a redundant rule is preferred over switching it off"
metadata:
  type: feedback
---

# Refactor from first principles; do not keep compatibility

Stated directly on 2026-09-03, mid-refactor of the reviewer-discovery rule
layer: **"第一性原理 不要向后兼容 抛弃历史包袱"** — first principles, no backward
compatibility, discard the legacy baggage.

## How to apply it

- **Change signatures and config keys outright.** Do not add a shim, an alias,
  or a deprecated path. `eligibility.assess(conn, person, policy, now_year=)`
  became `assess(record, policy)`; `min_academic_age` / `max_academic_age` /
  `[seniority.career]` were deleted rather than mapped forward. Update the
  tests to the new shape instead of preserving the old call.
- **Delete a redundant thing; do not set it to `off`.** When told to remove the
  invitation-response rule the user meant *delete* — asked again about the
  veteran rule, the answer was the same. A rule that cannot distinguish itself
  from another is not worth a config switch.
- **State a quantity once.** The user's own instinct spotted two rules
  measuring one career length ("重复啊！"), which turned out to be worse than
  duplication: two derivations from two sources, disagreeing for 158 of 197
  candidates. Expect this class of question and go looking for the rest — dead
  duplicate config keys (`geo.bonus`) and duplicated hardcoded thresholds
  (identity confidence at both 0.6 and 0.8) were found the same way.
- **Answer "is this configurable?" with a table, and say what is deliberately
  fixed and why.** That framing is what they asked for when surveying
  constraints, not just a list of keys.

## The tone they want back

Analysis before code on open-ended questions, and an honest verdict when asked
whether an architecture is good enough — "是不是你架构不够第一性原理" expects a
direct answer about what is and is not sound, with the evidence, not a defence.
