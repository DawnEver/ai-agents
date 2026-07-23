"""General-purpose web crawler — fetch-and-parse with pagination support.

Provides reusable building blocks for crawling academic and institutional
web pages.  Domain-specific scraping logic is injected via callable *parser*
arguments rather than baked in.
"""

from __future__ import annotations

import random
import time
from typing import Any, Callable

import requests
from bs4 import BeautifulSoup

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
DEFAULT_DELAY: tuple[float, float] = (0.5, 2.0)  # (min, max) seconds


def _build_session(headers: dict[str, str] | None = None) -> requests.Session:
    """Create a :class:`requests.Session` with sensible browser-like defaults."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9",
        **(headers or {}),
    })
    return session


def crawl_page(
    url: str,
    parser: Callable[[BeautifulSoup, str], list[dict[str, Any]]],
    session: requests.Session | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
    delay: tuple[float, float] = DEFAULT_DELAY,
) -> list[dict[str, Any]]:
    """Fetch *url*, parse with *parser*, and return extracted records.

    Parameters
    ----------
    url:
        Target page URL.
    parser:
        Callable that receives a parsed :class:`BeautifulSoup` tree and the
        final URL (after redirects).  Must return ``list[dict]``.
    session:
        Reusable session.  A new one is created when omitted.
    headers:
        Extra HTTP headers merged into the session defaults.
    timeout:
        Request timeout in seconds.
    delay:
        ``(min, max)`` seconds to pause before the request.
    """
    sess = session or _build_session(headers)
    wait = random.uniform(delay[0], delay[1])
    if wait > 0:
        time.sleep(wait)

    resp = sess.get(url, timeout=timeout)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    return parser(soup, resp.url)


def crawl_paginated(
    base_url: str,
    parser: Callable[[BeautifulSoup, str], list[dict[str, Any]]],
    max_pages: int = 5,
    url_builder: Callable[[str, int], str] | None = None,
    session: requests.Session | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
    delay: tuple[float, float] = DEFAULT_DELAY,
) -> list[dict[str, Any]]:
    """Crawl multiple pages derived from *base_url*, collecting parsed records.

    Parameters
    ----------
    base_url:
        Starting URL.  Passed to *url_builder* as the first argument.
    parser:
        Same contract as :func:`crawl_page`.
    max_pages:
        Hard stop after this many pages (1-indexed).
    url_builder:
        Receives ``(base_url, page_number)`` and returns the page URL.
        Defaults to ``f"{base_url}?page={page_number}"``.
    session:
        Reusable session shared across all pages.
    headers:
        Extra HTTP headers.
    timeout:
        Per-request timeout.
    delay:
        ``(min, max)`` seconds to pause between pages.
    """
    sess = session or _build_session(headers)
    build = url_builder or (lambda base, n: f"{base}?page={n}")
    all_records: list[dict[str, Any]] = []

    for page in range(1, max_pages + 1):
        url = build(base_url, page)
        records = crawl_page(
            url, parser, session=sess, timeout=timeout, delay=delay
        )
        if not records:
            break
        all_records.extend(records)

    return all_records
