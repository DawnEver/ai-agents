---
name: attribute-inference-scope-2026-09-17
description: inferring a per-entity attribute by voting over the record's whole entity set attributes every member to the record's aggregate — scope the evidence to the entity's own line
metadata:
  type: engineering
---

# Aggregate scope contaminates per-entity attribution

`created: 2026-09-17, accessed: 2026-09-17`

A dataset of records, each carrying a *set* of entities, where an attribute is
needed per entity but is stated nowhere directly — so it has to be inferred by
majority vote over the records each entity appears in.

The first implementation voted using **every co-entity named in the record**.
That is wrong whenever a record aggregates entities from different places: an
entity's inferred attribute ends up reflecting whichever group its co-entities
mostly belong to, not what it is itself. The failure is silent and looks
plausible — the vote has a clear winner, it is just the wrong one. In this case
a university was attributed to a country it has no connection to, purely
because the papers it appeared in were collaborations with that country.

## The rule

**Scope the evidence to the smallest unit that plausibly carries the
attribute, and fall back to the wider scope only when the narrow one is
empty.**

Here: pair each entity with the attribute values found on *its own line*, and
only when its line names none does the record's full set get consulted. That
single change moved the misattributed entry to the correct value while leaving
the genuinely co-located cases alone.

Two checks worth running on any such inference:

- **Spot-check the entries you can verify independently.** A handful of
  well-known cases is enough to show whether the vote is tracking the entity or
  its neighbourhood. This is what caught it — the aggregate picture looked fine.
- **Prefer no answer to a borrowed one.** An entity whose own line is silent is
  better left unknown than assigned its collaborators' attribute. The fallback
  above is a deliberate widening, not a default.
