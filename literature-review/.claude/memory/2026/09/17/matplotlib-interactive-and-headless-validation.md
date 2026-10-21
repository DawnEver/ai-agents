---
name: matplotlib-interactive-and-headless-validation-2026-09-17
description: matplotlib 3.10 API removals and guards, dependency-free hover tooltips, and how to validate a plt.show() script headlessly
metadata:
  type: engineering
---

# Interactive matplotlib: API drift, hover, headless validation

`created: 2026-09-17, accessed: 2026-09-17`

Building a `plt.show()` script on matplotlib 3.10.9. Each of these is a small
thing that costs a round trip if unknown.

## API drift on current matplotlib

- **`matplotlib.cm.get_cmap` was removed in 3.9, not merely deprecated.** Code
  written against older examples — including the two-argument
  `get_cmap(name, n)` form for a discretised colormap — raises `AttributeError`.
  The replacement is the registry:
  `matplotlib.colormaps["tab20"].resampled(n)`.
- **`plt.Rectangle` resolves at runtime but is not a public export.** Import it
  from `matplotlib.patches`. (Pyright flags the pyplot form as
  `reportPrivateImportUsage`; the runtime tolerates it, which is why this one
  survives until a linter or a matplotlib cleanup catches it.)
- **`fig.canvas.manager` can be `None`**, so `manager.set_window_title(...)`
  needs a guard — a non-GUI backend has no window to name.

## Hover tooltips need no extra dependency

`mplcursors` is not required. Hide an `ax.annotate` with a bbox, connect
`motion_notify_event`, and test each patch directly:

```python
contains, _ = patch.contains(event)   # event is the MouseEvent
```

On a hit, move the annotation to the bar's end, set its text, and
`fig.canvas.draw_idle()`; otherwise hide it. This works for `barh` patches as
readily as for scatter points.

## Validating an interactive script headlessly

Replace `plt.show` before the script reaches it, then save every open figure
under the Agg backend:

```python
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
def fake_show(*a, **k):
    for num in plt.get_fignums():
        plt.figure(num).savefig(f"_check{num}.png", dpi=70, bbox_inches="tight")
plt.show = fake_show
runpy.run_path("script.py", run_name="__main__")
```

This catches rendering errors without a window, and the saved PNGs can be read
back to confirm the chart actually looks right — which is how a wrong colour
mapping was caught that no exception would have surfaced.

**Caveat:** if the script ends in `raise SystemExit(main())`, running it with
`run_name="__main__"` exits the process at that line. Any verification code
placed *after* the `runpy` call never executes. Do the checks in a separate
process, or inside the fake `show`.
