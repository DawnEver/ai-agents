---
name: publisher-download-session-2026-09-22
description: The working recipe for authenticated publisher PDF downloads via lit-review, including three CLI facts the playbook gets wrong
metadata:
  type: engineering
---

# Authenticated publisher download — the recipe that actually works

`created: 2026-09-22, accessed: 2026-09-22`

Getting paywalled PDFs through `lit-review acquire` has four non-obvious parts.
All four were verified against the source, because the skill playbook disagrees
with the code on three of them.

## The recipe

```bash
# 1. Open a headed browser on the publisher site and log in through the
#    institution, then CLOSE THE WINDOW. The command returns when it closes.
uv run --project "<plugin-root>" lit-review login \
    --profile <name> --browser-channel chrome --url <publisher-home>

# 2. Download. Note: this one takes a PATH, not the name used above.
uv run --project "<plugin-root>" lit-review acquire \
    --topic <slug> --approved-by <you> \
    --profile "<LOCALAPPDATA>/literature-review/browser-profiles/<name>" \
    --limit 20
```

## The four facts

**1. `login --profile` takes a NAME; `acquire --profile` takes a PATH.** They are
different parameters with the same spelling. `login` expands a non-absolute name
to `<LOCALAPPDATA>/literature-review/browser-profiles/<name>`; `acquire` uses the
string as a filesystem path and fails with `WinError 3: cannot find the path
specified` if given a bare name. The playbook shows `<name>` for both.

**2. Their `--browser-channel` defaults disagree, and `login`'s default is the
broken one.** `login` defaults to `chromium` — Playwright's bundled build, which
on a machine where only the real browser is installed prints the
"playwright install" banner and, because the failure surfaces inside a piped
command, exits 0 having done nothing. `acquire` defaults to `chrome`, the real
installation. Pass `--browser-channel chrome` explicitly to `login`.

**3. A plain HTTP fetch of a publisher PDF endpoint fails even from a campus
IP** (a redirect-following request returned 502). Network position is not
access; the browser session is. But the session is not optional even when the
institution authenticates by IP — the *cookies* are what the download transport
presents.

**4. What makes the automated download work is a profile that has passed the
bot check once.** A fresh automated browser context lands on the interstitial
and sits there indefinitely. A profile saved after a human cleared it does not.
This is the whole reason the browser path exists.

## Diagnostics worth keeping

- **Cookies live at `<profile>/Default/Network/Cookies`.** The SQLite file is
  locked while the browser is open, so a successful copy is itself proof the
  browser is still running. Copy it aside before reading; never read in place.
- **A zero-byte output file plus a browser window titled with a bot-check
  interstitial means stalled, not slow.** Stdout is block-buffered when
  redirected, so a long silent run is *not* by itself evidence of a hang — but
  that specific combination is. Check the window title before waiting longer.
- **`--limit` is capped at 20**; a larger value aborts the run.
- **A profile lock is the only trigger for the force-kill of every browser
  process on the machine.** That path is reachable from the download helper, not
  from `login` — see the sibling entry on playbook drift.

## Cross-check after a run

Confirm the artifact is real before trusting the count: the manifest carries a
`pdf_path` per item, and a genuine PDF starts with `%PDF-` and is megabytes, not
kilobytes. A "downloaded=1" line with a 2 KB file is an error page wearing a
success message.

## Files

- `src/academia/litreview/acquire/download.py` — `open_login`, `playwright_page`,
  `_kill_stale_chrome`, `_is_profile_lock_error`
- `src/academia/cli/lit_review.py` — the `login` and `acquire` subparsers
  (their `--profile` semantics differ)
