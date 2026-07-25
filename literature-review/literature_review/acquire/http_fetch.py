"""Browser-free PDF retrieval.

Institutional repositories and preprint servers serve PDFs over plain HTTP with
no bot challenge, so driving a browser at them is slow and — because it depends
on CSS selectors matching a visible button — unreliable. This module resolves a
URL to a PDF using only HTTP: fetch it, and if it turns out to be a landing
page, read the PDF link out of the HTML and fetch that.

Only when this fails does the caller pay for a Playwright session.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests

from literature_review.providers.base import polite_user_agent

TIMEOUT = 60
MAX_LINKS_PER_PAGE = 5
"""Cap on landing-page links followed, so a link farm cannot stall the run."""

BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

# Path markers that identify a PDF payload even without a .pdf suffix.
_PDF_PATH_MARKERS = (
    "/bitstream/", "/bitstreams/", "/portalfiles/", "/files/", "/content/pdf/", "/stamppdf/",
    "/ws/files/", "/pdf/", "/download",
)


def _get(url: str, session: Any = None, referer: str = "", **kwargs: Any) -> Any:
    """Single seam for HTTP GET — tests patch this."""
    headers = {
        "User-Agent": BROWSER_UA,
        "Accept": "application/pdf,text/html;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9",
        "X-Contact": polite_user_agent(),
    }
    if referer:
        # Repository file endpoints (Pure, DSpace) reject hotlinked requests;
        # arriving "from" the landing page is what a real reader looks like.
        headers["Referer"] = referer
    getter = session.get if session is not None else requests.get
    return getter(url, timeout=TIMEOUT, allow_redirects=True, headers=headers, **kwargs)


def _is_pdf_url(url: str) -> bool:
    path = (urlparse(url.lower()).path or "")
    return path.endswith(".pdf") or any(marker in path for marker in _PDF_PATH_MARKERS)


def extract_pdf_links(html: str, base_url: str) -> list[str]:
    """Return absolute PDF URLs found in *html*, best candidate first."""
    found: list[str] = []

    # citation_pdf_url is the Highwire/Google-Scholar standard: the site telling
    # us exactly where its PDF is. Always outranks link guessing.
    for match in re.finditer(
        r'<meta[^>]+name=["\']citation_pdf_url["\'][^>]+content=["\']([^"\']+)["\']',
        html, re.IGNORECASE,
    ):
        found.append(urljoin(base_url, match.group(1)))
    for match in re.finditer(
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']citation_pdf_url["\']',
        html, re.IGNORECASE,
    ):
        found.append(urljoin(base_url, match.group(1)))

    for match in re.finditer(r'href=["\']([^"\']+)["\']', html, re.IGNORECASE):
        href = match.group(1)
        if _is_pdf_url(href):
            found.append(urljoin(base_url, href))

    seen: set[str] = set()
    unique: list[str] = []
    for url in found:
        if url not in seen:
            seen.add(url)
            unique.append(url)
    return unique


def _save_if_pdf(response: Any, target: Path) -> str | None:
    if getattr(response, "status_code", 0) != 200:
        return None
    body = response.content or b""
    # Trust magic bytes, not Content-Type: repositories mislabel PDFs as
    # octet-stream, and paywalls return login HTML labelled application/pdf.
    if not body.lstrip()[:5].startswith(b"%PDF-"):
        return None
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body)
    return str(response.url or "")


def fetch_pdf(
    url: str,
    target: Path,
    follow_landing_page: bool = True,
    session: Any = None,
    referer: str = "",
) -> str | None:
    """Download the PDF at *url* into *target*; return its source URL or None.

    Returning None means "try another strategy" — never an error, because the
    browser fallback still has a chance.
    """
    if not url:
        return None
    # One session across landing page and file request, so cookies set by the
    # landing page are presented when the file endpoint checks them.
    if session is None:
        session = requests.Session()
    try:
        response = _get(url, session=session, referer=referer)
    except Exception:  # noqa: BLE001 - network failure just means "try the browser"
        return None

    saved = _save_if_pdf(response, target)
    if saved is not None:
        return saved or url

    if not follow_landing_page or getattr(response, "status_code", 0) != 200:
        return None

    # Landing page: pull the PDF link out of the HTML and fetch it directly.
    try:
        html = response.text
    except Exception:  # noqa: BLE001
        return None

    base = str(getattr(response, "url", "") or url)
    for link in extract_pdf_links(html, base)[:MAX_LINKS_PER_PAGE]:
        if link == url:
            continue
        found = fetch_pdf(
            link, target, follow_landing_page=False, session=session, referer=base,
        )
        if found is not None:
            return found
    return None
