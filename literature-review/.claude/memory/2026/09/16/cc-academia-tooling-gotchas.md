---
name: cc-academia-tooling-gotchas-2026-09-16
description: Silent-failure traps in cc-academia — env vars and brief criteria that are never read, uv sync dropping extras, playwright channel, and where the browser capability actually lives
metadata:
  type: engineering
---

# cc-academia silent-failure traps

`created: 2026-09-16, accessed: 2026-09-16`

Five ways this toolchain fails *without erroring*, plus the plugin tree layout.

## 1. The workspace `.env` is not read for `ACADEMIA_CONTACT` or `S2_API_KEY`

Both are read **only** from the process environment:

- `src/academia/core/paths.py:271` — `os.environ.get("ACADEMIA_CONTACT")`
- `src/academia/sources/semantic_scholar.py:32` — `os.environ.get("S2_API_KEY")`

The only `.env` files consulted are plugin-internal: `src/.env` for AI provider
keys (`ai.py:111` — note `parents[2]` resolves to `src/`, i.e. *inside the
plugin*) and plugin-root/config `.env` for Zotero.

Verified by diffing `academia doctor` with and without the var exported: with
only the workspace `.env` populated it still warns `ACADEMIA_CONTACT is unset`;
exported as a real variable, the warning disappears.

So the README's `.env` table is misleading for these two. Set them as real
environment variables (`setx`, or export in the shell).

## 2. `inclusion_criteria` under `[constraints]` is silently dropped

`ResearchBrief.from_dict` lifts exactly four keys out of a nested `constraints`
table — `year_from`, `year_to`, `content_types`, `preferred_venues` — and
ignores everything else. Because TOML assigns every key after a `[constraints]`
header to that table, a brief written with `inclusion_criteria` /
`exclusion_criteria` below it loads with **empty criteria**: screening runs with
no standard at all, and nothing warns.

Put them at **top level**, before the first `[table]` header. A brief written
the nested way loads without error and screens with no criteria, so the mistake
is invisible unless you check.

Check with:
```python
ResearchBrief.from_dict(tomllib.load(open(path,'rb'))).inclusion_criteria
```
Empty list on a brief that visibly has criteria means they are nested.

## 3. `uv sync --extra X` uninstalls every other extra

`uv sync` makes the environment match *exactly* the requested set. Syncing with
only `--extra browser` silently removed `pdf` and `embed`. Use `--all-extras`.

Canonical env is `~/.cache/cc-academia/venv`, set by the plugin's own
`.claude/settings.json` via `UV_PROJECT_ENVIRONMENT`. Other venvs on this
machine (e.g. under `~/.local/share/`) carry playwright but **not** the plugin —
`uv run --project <plugin-root>` is what actually runs it.

Verify with `uv run --project <root> academia doctor`; the `extras:` line should
list all of `ai, browser, pdf, plot, embed`.

## 4. Playwright: pin mismatch and the cookie trap

- The bundled-Chromium build is version-pinned. A newer playwright wants a
  `chromium-<n>` that is not downloaded and raises
  `Executable doesn't exist at ...\ms-playwright\chromium-1234\...`. Passing
  `channel="chrome"` uses the system Chrome and avoids the download entirely.
- **Session reuse needs `lit-review login --profile <name>`.** `--browser-channel`
  alone launches a fresh temporary context with zero cookies. (Already recorded
  in `ieee-xplore-pdf-selector-fix`, 2026-08-01 — repeated here because it is
  easy to lose.)

## 5. The browser capability is acquire/rev-disc only — `search` has none

`grep` for `browser|playwright` across `src/academia/sources/` and
`src/academia/litreview/search.py` returns **nothing**. All browser wiring lives
in:

| Location | Purpose |
|---|---|
| `litreview/acquire/engine.py:218` | PDF download |
| `cli/rev_disc.py:490` | publisher pages for reviewer discovery |
| `reviewer/contact.py:77` | contact discovery |

`lit-review search` exposes only `--topic --provider --max-pages
--rows-per-page --delay --probe-only --skip-probe` — no `--browser`, no
`--profile`. Driving a source through a browser therefore requires a script
outside the plugin; `playwright_page()` in `acquire/download.py:151` returns
`(page, close)` and is the reusable building block.

## Plugin tree layout

cc-academia resolves from the marketplace checkout —
`~/.claude/plugins/marketplaces/cc-market/cc-academia` (source
`github.com/DawnEver/cc-market`, `autoUpdate: true`), currently **0.1.15**, with
an identical mirror at `~/.claude/plugins/cache/cc-market/cc-academia/0.1.15/`.
`uv run --project` uses the **marketplace** path, so that is the tree to patch.
Note hooks load from the *cache* path with the version in it
(`cache/cc-market/rem/1.1.18/...`), so the two layouts are not
interchangeable when reading paths out of hook output.

## Files

- `src/academia/core/paths.py`, `src/academia/sources/semantic_scholar.py`
- `src/academia/litreview/models.py` — `ResearchBrief.from_dict`
- `src/academia/acquire/download.py` — `playwright_page`, `open_login`
