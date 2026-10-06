---
name: interactive-means-live-window-2026-09-17
description: user preference — "交互式" charts means a live plt.show() GUI window, not an HTML page; ask which before building
metadata:
  type: preference
---

# "交互式" means a live window, not an HTML page

`created: 2026-09-17, accessed: 2026-09-17`

Asked for 交互式 (interactive) charts, the first implementation produced
standalone HTML using a JavaScript charting library — hoverable, zoomable,
self-contained, and entirely the wrong thing. It was rejected outright, and
what was wanted was `matplotlib` with `plt.show()`: a real GUI window with the
toolbar.

The same correction also rejected a choropleth world map in favour of plain
ranked bar charts — so the push was toward *simpler*, not richer.

## The rule

**"Interactive" is ambiguous between a rendered web page and a live GUI
window, and the two are a full rebuild apart.** Confirm which before building.
When the user is working in a Python/matplotlib context, read it as
`plt.show()` unless told otherwise.

Corollary: when a request specifies a chart type or family, resist upgrading it
to the richest thing available. The elaborate option is not a bonus if it is
not what was asked for — it is a rewrite plus a dependency the user then has to
carry (the JavaScript charting library installed for the rejected version was
never used).

Signals that a live window is meant: the surrounding work is scripts and data
files rather than a web app, the user will run the command themselves, and
"interactive" is contrasted with *static images* rather than with *static
HTML*.
