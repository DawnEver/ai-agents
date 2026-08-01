---
name: ieee-xplore-pdf-selector-fix-2026-08-01
description: IEEE Xplore PDF download selector drift — why paywalled IEEE papers silently failed in acquire, and the fix
metadata:
  type: engineering
---

# IEEE Xplore PDF button selector drift

`created: 2026-08-01, accessed: 2026-08-01`

## Symptom

`lit-review acquire` browser transport could log into IEEE Xplore (page fully
loaded, "Download PDF" button present, session valid on campus IP) yet every
IEEE paywalled paper ended `not_found` — no PDF captured, no access-wall error,
no Cloudflare block. Papers from Open Access (IEEE Access) still worked because
their `ielx7` direct links are plain HTTP.

## Root cause

`PDF_BUTTON_SELECTORS` in `literature_review/acquire/transport.py` was stale.
IEEE Xplore rebuilt its Angular app; the current download button is:

```html
<a class="xpl-btn-pdf" href="/stamp/stamp.jsp?tp=&arnumber=<n>">PDF</a>
```

The old selectors matched `a[href*="/stampPDF/"]`, `xpl-download-pdf`,
`a[xpl-download-pdf]` — none of which exist anymore. So `_from_pdf_button`
found nothing, and `_from_ieee_iframe` (which looks for
`iframe[src*="stampPDF/getPDF.jsp"]`) never ran because the button strategy
returned None before reaching it — actually the button click on a stale selector
silently did nothing and the strategy chain moved on.

## Fix (2026-08-01)

Added two selectors to `PDF_BUTTON_SELECTORS`:

```python
".xpl-btn-pdf",                    # current IEEE Xplore download button (Angular, 2023+)
'a[href*="/stamp/stamp.jsp"]',     # IEEE stamp.jsp PDF endpoint (current)
```

End-to-end verified: `BrowserTransport.fetch` on `document/10538094/` returns
`stampPDF/getPDF.jsp?...` and writes a valid `%PDF-1.5` file (~6 MB). The
stamp.jsp wrapper page JS-renders an iframe pointing at
`/stampPDF/getPDF.jsp?tp=&arnumber=<n>&ref=...`, which `_from_ieee_iframe`
then fetches.

## Gotchas

- **Session reuse needs `--profile`.** `--browser-channel chrome` alone launches
  a fresh temporary context with zero cookies. Run
  `lit-review login --profile <name> --completion browser-close` once, then
  `acquire --profile <name>`. Docs in AGENT.md / 03-acquire.md updated to say this.
- **IEEE stamp.jsp is a JS wrapper**, not the PDF itself. Navigating to it
  directly returns HTML with `apm_do_not_touch` scripts; the real PDF comes via
  the `stampPDF/getPDF.jsp` iframe after JS runs (~8 s).
- **`%PDF-` magic**: verify.py uses `PDF_MAGIC = b"%PDF-"` (5 bytes). A naive
  `b[:5] == b'%PDF'` check is wrong.
- **IEEL pdf button is `xpl-btn-pdf` not `xpl-download-pdf`** — the two are
  easy to confuse; the former is the visible button, the latter was pre-2023.

## Files

- `literature_review/acquire/transport.py` — `PDF_BUTTON_SELECTORS` (+2)
- `literature_review/cli.py` — import-screening out_dir fix + stale-dir migration
- Docs: `AGENT.md`, `.claude/skills/literature-review/03-acquire.md` (profile requirement)
