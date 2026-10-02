# 02 — Write deck.toml

Full reference: the docstring at the top of `scripts/build_slides.py`.

```toml
template = "src/Template.pptx"
base = "figures"                       # images resolve here

[patterns.three-up]
slide = 19
# static = ["Logo"]

[[slides]]
keep = 1                               # template cover, unchanged

[[slides]]
pattern = "three-up"
title = "Efficiency Map"
images = ["map_efficiency.png", "lines_efficiency.png", { path = "cells_efficiency.png", fit = "cover" }]
texts = ["Line one\n  indented **bold** line"]
notes = "Speaker notes"
```

Guidance:

- **Group inputs by meaning, fill by slot.** E.g. 18 figures named `{map,lines,cells}_<quantity>.png`
  → one slide per quantity, the three views in slots 0/1/2. State the grouping to the user.
- Order slides the way the user will talk through them; say which order you chose.
- Titles: derive from inputs (`total_loss_w` → "Total Loss Map"); don't add claims, platform names
  or conclusions that aren't in the inputs.
- `""` leaves a slot empty (it is dropped, not left with template content).
- Too many items for a pattern is an error — pick or define a pattern with more slots instead.
- For long, regular series, it is fine to generate `deck.toml` with a short script; the TOML stays
  the reviewed artefact.
