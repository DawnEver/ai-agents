---
name: ieee-xplore-search-payload-drift-2026-09-16
description: IEEE Xplore /rest/search ignores the payload the plugin sends and answers 200 with front-matter records — the correct contract, and the browser-driven workaround
metadata:
  type: engineering
---

# IEEE Xplore search payload drift

`created: 2026-09-16, accessed: 2026-09-16`

## Symptom

`lit-review search --provider ieee_xplore` returns HTTP 200, a plausible
`totalRecords`, and total rubbish: conference digests, "Book of abstracts",
book front matter, "The Princeton Companion to Applied Mathematics". Same five
titles come back for unrelated queries — Q19 and Q21 returned *identical*
result sets, which is the tell that the query is being ignored rather than
mis-ranked.

`_guard()` in `src/academia/sources/ieee.py` does not fire: the body contains
`records`, so it looks like a valid payload and nothing raises.

## Root cause

The posted payload is `{queryText, newsearch, pageNumber, rowsPerPage,
searchField}`. The endpoint no longer honours that schema; it falls back to
some default catalogue listing.

**It is not a session problem.** Reproduced identically from plain HTTP *and*
from a `fetch()` executed inside an authenticated, Cloudflare-cleared browser
page on a campus IP. The contract moved; the cookie jar is irrelevant.

This is the same *family* of bug as `ieee-xplore-pdf-selector-fix` (2026-08-01)
— IEEE rebuilt the front end and the client kept sending the old shape. Expect
more of these; the durable fix is to re-capture from the site, not to guess.

## The correct payload

Captured from the site's own UI by listening for its XHR (see below):

```json
{
  "queryText": "...",
  "highlight": true,
  "returnFacets": ["ALL"],
  "returnType": "SEARCH",
  "matchPubs": true
}
```

No page number, no rows-per-page, no searchField.

## Recovering a drifted contract

Do not guess the new shape — record it. Launch the browser, attach
`page.on("request", ...)`, navigate to the site's own search URL, let the SPA
fire its XHR, and print `req.post_data_json` for URLs containing `/rest/search`.
Also scrape the rendered DOM titles in the same run: if the UI shows real hits
while your request does not, the fault is in your payload, not in the endpoint
or the network. That single comparison decides the whole diagnosis.

## Workaround when search is unusable

Drive the POST from inside an authenticated page context so cookies, `Origin`,
`User-Agent` and the network position all match:

```python
page, close = playwright_page(None, "chrome", "direct")   # from acquire/download.py
page.goto("https://ieeexplore.ieee.org/search/searchresult.jsp")
res = page.evaluate(SEARCH_JS, ["https://ieeexplore.ieee.org/rest/search", payload])
```

The plugin has no browser path in `search` (see the tooling entry), so this
needs a script outside the plugin.

## Files

- `src/academia/sources/ieee.py` — `IeeeXplore.search()` payload (stale)
- `src/academia/acquire/download.py` — `playwright_page()`, the reusable page helper
