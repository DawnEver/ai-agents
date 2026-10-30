# Analysis presentations

Use this reference for result-led scientific and engineering decks, not as a mandatory
structure for every presentation. Keep project numbers and physical/model definitions in
their authoritative data sources, not in this skill.

## Plan the comparison, not a feature demonstration

- Agree the comparison questions and chapter boundaries before assembling figures. A result
  deck should show measured or simulated outcomes, not substitute software screenshots,
  implementation diagrams, or successful execution for scientific evidence.
- When the user asks for conclusion-first comparisons, put a concise conclusion slide
  immediately before **each** comparison block. State the observed trade-off and its scope;
  then show the supporting response, spectra, and losses. Do not invent a conclusion just
  to fill the pattern.
- When losses are part of the question, place the corresponding loss breakdown on the
  comparison slide or directly beside/after its response plots, rather than collecting all
  losses in a detached final chapter. Keep operating point and case identities matched.
- Let the evidence determine the slide count. A requested chapter structure is not permission
  to compress unreadable comparisons or pad the deck with feature-proof slides.

## Make each figure independently interpretable

- Put the comparison conditions visibly with the figure: operating point, configurations,
  varied parameter, shared controls, units, retained window, and qualification status as
  relevant. Speaker notes and an opening conditions slide are not substitutes for conditions
  needed to interpret a later figure.
- Prefer pairs or small multiples when five overlaid traces hide the differences. Keep common
  scales and case colours where meaningful; show full context plus a clearly labelled detail
  window instead of silently cropping away an inconvenient transient.
- For dense spectra, prefer sparse, separated frequency bars and clearly labelled frequency
  ranges or panels. Preserve actual bins, amplitudes, normalization and units. Disclose any
  omitted range or selection; never move peaks, alter values, or fit a shift to improve visual
  agreement. Rounding for display must not replace full-precision archived results.
- Use audience-facing, method-neutral names when requested, for example **Magnet losses**.
  Renaming a presentation label does not change the calculation: retain its exact method,
  convention and provenance in the source archive, and expose distinctions when they affect
  the comparison. Do not combine incompatible loss definitions under one label.
- When individual operating behaviour matters, provide case-level pages alongside the
  comparisons: startup, command tracking, trajectories, retained-window metrics and the
  actual case conditions. A comparison overlay is not a substitute for a case's own run.
  Distinguish close mean tracking from cycle-to-cycle repeatability, and requested signals
  from applied/measured signals; an averaged voltage trajectory does not prove clipping.

## Match claims to evidence

- Distinguish actual acquisition origin from tool capability. An externally orchestrated run
  must not be relabelled as a native workflow merely because the official tools could perform
  that class of analysis.
- A custom diagnostic should present an actual diagnostic result, with its limitations, not
  imply that the underlying physics is unavailable in the vendor tool. **Not verified**, **not
  exposed by the tested interface**, and **impossible** are different claims.
- Preserve finite-window, unmatched-protocol and unqualified labels. Agreement in one scalar
  does not establish waveform equivalence, repeatability, a physical rating or optimality.
  Record source identities/hashes so redrawn plots remain traceable to unchanged numbers.

## Apply per-deck choices explicitly

Requirements such as no speaker notes, no repetitive caveat footers, conclusion-first blocks,
or particular terminology belong to the current deck specification, not universal defaults.
For a no-notes deck, omit generated notes; keep essential conditions in visible captions and
technical provenance in a separate archive. If repeated footers are banned, use compact
case-specific conditions or a definitions page without hiding material limitations.

## Preserve the template while adapting it

- Reuse the user's typography and layout rather than redesigning the template. If text size
  must change, inspect run-level formatting as well as paragraph/theme defaults: a run-level
  font size can override the apparent placeholder setting. Verify the rendered result.
- When deriving a pattern that resizes a placeholder, first resolve its inherited geometry
  from the slide/layout/master and materialize a **complete** local transform (position and
  extent) before changing dimensions. A partial local `xfrm` can discard inherited placement.
  Make such adaptations on a task-local template copy, never the original.
- Review the contact sheet and individual dense slides at delivery scale. Check figure
  captions, legends, bar separation, table text and axes, not only slide titles or lint output.
