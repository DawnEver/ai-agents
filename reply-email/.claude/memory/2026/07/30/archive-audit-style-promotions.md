# Full-archive audit → style promotions (2026-07-30)

Method: read **all** archived `meta.md` files (27 at the time), extract every `## Diff notes`
entry, group by theme, and compare each recurring theme against `style/profile.md` (rules +
Last-checked log). Promote anything meeting the ≥2-archive threshold.

Why: the per-round diff-learning step records each edit as "single instance, no promotion"
in isolation. Cross-round recurrence only becomes visible when the whole archive is read at
once — per-round archiving systematically under-promotes. One meta had even annotated "second
instance" in its own diff notes while the Last-checked log still recorded it as single.

How to apply: run this audit periodically (or whenever the Last-checked log grows long):

1. Glob `archived/**/meta.md`, read all diff notes (an Explore subagent works well).
2. Group edits by theme; count distinct archives per theme.
3. Promote ≥2 themes to `style/profile.md` rules + `## Last updated`; leave singles in place.
4. Also audit committed spec files against actual archive data for drift (naming, schema,
   duplicated conventions between AGENT.md and command files).

Promoted this round (evidence in archived meta.md diff notes):

- Inline phrasing ("…are below" / "shown below") over "I've attached" (2026-06-23, 2026-07-25)
- Short sentences; split em-dash / compound run-ons (2026-06-09, 2026-06-22)
- No echo-back of the sender's own formulas/numbers; conclusion stated once, firmly
  (2026-07-15, 2026-07-16)
- No self-deprecation / self-critical admissions (2026-07-15, second instance per its meta)
- Concrete references over vague promises (2026-07-13, 2026-07-15)
- Closing-invitation exception for outgoing-initiated mail written into the rules (2026-07-20)

Spec fixes made alongside: AGENT.md legacy-quirks section (early `original.md`, `position:`
field, `-v2` orphan dir), attachments documented, `prev:` canonicalized to repo-root-relative,
command files slimmed to procedural glue + explicit "wait for 归档" gate, archive.md step
order aligned with AGENT.md 7a–7e, reply-style.md example brought in line with the
blank-line formatting rule and no-closing-invitation rule.
