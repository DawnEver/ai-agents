"""DBLP provider adapter.

Implements BaseProvider for the DBLP Computer Science Bibliography REST API.
Free — no API key required. Definitive CS bibliography covering all major
venues (ACM, IEEE, SIAM, Springer, etc.).

Note: DBLP does NOT provide abstracts. Candidates from DBLP should be
cross-referenced with other sources for abstract-level screening.

API docs: https://dblp.org/faq/How+to+use+the+dblp+search+API.html
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from literature_review.providers.base import (
    BaseProvider,
    ProbeResult,
    ProviderError,
    SearchResult,
    polite_user_agent,
)

BASE_URL = "https://dblp.org/search/publ/api"
USER_AGENT = polite_user_agent()

# DBLP venue type mapping — used to classify content_type
VENUE_PATTERNS: dict[str, str] = {
    "conf/": "Conferences",
    "journals/": "Journals",
    "series/": "Book Chapters",
    "phd/": "Theses",
    "books/": "Books",
    "reference/": "Reference",
}


def _as_text(value: Any) -> str:
    return str(value or "").strip()


def _optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _classify_venue_type(venue_url: str) -> str:
    """Guess content_type from DBLP venue key pattern."""
    for prefix, label in VENUE_PATTERNS.items():
        if prefix in venue_url.lower():
            return label
    return ""


def _build_url(
    expression: str,
    first: int = 0,
    hits: int = 25,
    year_from: int | None = None,
    year_to: int | None = None,
) -> str:
    """Build a DBLP search API URL."""
    from urllib.parse import quote, urlencode

    params: dict[str, Any] = {
        "q": expression,
        "format": "json",
        "h": hits,
        "f": first,
    }
    return f"{BASE_URL}?{urlencode(params, quote_via=quote)}"


def _api_get(url: str, timeout_seconds: int = 30) -> dict[str, Any]:
    """Execute a GET request to the DBLP API."""
    request = Request(
        url,
        method="GET",
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            body_text = response.read().decode("utf-8", errors="replace")
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        if error.code == 429:
            raise ProviderError("rate_limited", "dblp", {"status": 429}) from error
        raise ProviderError(
            f"http_{error.code}", "dblp", {"status": error.code},
        ) from error
    except URLError as error:
        raise ProviderError(
            f"network_error: {error.reason}", "dblp",
        ) from error

    try:
        data = json.loads(body_text)
    except json.JSONDecodeError:
        raise ProviderError("non_json_response", "dblp")

    if not isinstance(data, dict):
        raise ProviderError("unexpected_json_shape", "dblp")
    return data


def _extract_info(record: dict[str, Any]) -> dict[str, Any]:
    """DBLP wraps each hit in an 'info' dict — extract it."""
    return record.get("info", record) if isinstance(record, dict) else {}


def _extract_total(data: dict[str, Any]) -> int:
    result = data.get("result", {})
    hits_info = result.get("hits", {}) if isinstance(result, dict) else {}
    total = hits_info.get("total", 0) if isinstance(hits_info, dict) else 0
    return int(total) if isinstance(total, (int, str)) and str(total).isdigit() else 0


def _extract_records(data: dict[str, Any]) -> list[dict[str, Any]]:
    result = data.get("result", {})
    hits = result.get("hits", {}) if isinstance(result, dict) else {}
    hit_list = hits.get("hit", []) if isinstance(hits, dict) else []
    return hit_list if isinstance(hit_list, list) else []


def _extract_titles(data: dict[str, Any], limit: int = 5) -> list[str]:
    titles: list[str] = []
    for record in _extract_records(data)[:limit]:
        info = _extract_info(record)
        title = info.get("title")
        if isinstance(title, str) and title.strip():
            titles.append(title.strip())
    return titles


def _extract_authors(info: dict[str, Any]) -> list[str]:
    """DBLP authors can be a single object or a list of objects."""
    authors_raw = info.get("authors", {})
    if isinstance(authors_raw, dict):
        author_list = authors_raw.get("author", [])
    elif isinstance(authors_raw, list):
        author_list = authors_raw
    else:
        return []

    if isinstance(author_list, dict):
        author_list = [author_list]
    if not isinstance(author_list, list):
        return []

    result = []
    for a in author_list:
        if isinstance(a, dict):
            name = _as_text(a.get("text") or a.get("name") or str(a))
            if name:
                result.append(name)
    return result


def _filter_by_year(records: list[dict[str, Any]], year_from: int | None, year_to: int | None) -> list[dict[str, Any]]:
    """Client-side year filter (DBLP API doesn't support year range natively)."""
    if year_from is None and year_to is None:
        return records

    filtered = []
    for record in records:
        info = _extract_info(record)
        year = _optional_int(info.get("year"))
        if year is None:
            # Can't determine year — include and let screening decide
            filtered.append(record)
            continue
        if year_from is not None and year < year_from:
            continue
        if year_to is not None and year > year_to:
            continue
        filtered.append(record)
    return filtered


class DblpProvider(BaseProvider):
    """DBLP Computer Science Bibliography adapter.

    Uses the free DBLP search API. Returns JSON. Importantly, DBLP does
    NOT provide abstracts — only bibliographic metadata. Use for venue
    discovery and completeness checking, not for abstract screening.
    """

    @property
    def provider_name(self) -> str:
        return "dblp"

    def search(
        self,
        expression: str,
        query_id: str,
        page_number: int = 1,
        rows_per_page: int = 25,
        year_from: int | None = None,
        year_to: int | None = None,
        content_types: list[str] | None = None,
        sort: str | None = None,
        timeout_seconds: int = 30,
    ) -> SearchResult:
        """Execute a single page of search via DBLP API.

        DBLP uses first/hit-based pagination. Year filtering is client-side.
        """
        first = (page_number - 1) * rows_per_page
        # Request more hits than needed to account for client-side year filtering
        fetch_size = rows_per_page * 3 if (year_from or year_to) else rows_per_page
        url = _build_url(expression, first=first, hits=fetch_size)

        try:
            data = _api_get(url, timeout_seconds=timeout_seconds)
            raw_records = _extract_records(data)
            total = _extract_total(data)

            # Client-side year filtering
            filtered_records = _filter_by_year(raw_records, year_from, year_to)[:rows_per_page]

            return SearchResult(
                provider=self.provider_name,
                query_id=query_id,
                page_number=page_number,
                total_count=total,
                records=filtered_records,
                raw_response=data,
            )
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(str(exc), self.provider_name) from exc

    def probe(
        self,
        expression: str,
        query_id: str,
        year_from: int | None = None,
        year_to: int | None = None,
        content_types: list[str] | None = None,
        sort: str | None = None,
        timeout_seconds: int = 30,
    ) -> ProbeResult:
        """Probe page 1 with hits=5 for a quick estimate."""
        result = self.search(
            expression, query_id,
            page_number=1, rows_per_page=5,
            year_from=year_from, year_to=year_to,
            content_types=content_types, sort=sort,
            timeout_seconds=timeout_seconds,
        )
        titles = [
            _extract_info(r).get("title", "")
            for r in result.records[:5]
            if _extract_info(r).get("title")
        ]
        return ProbeResult(
            provider=self.provider_name,
            query_id=query_id,
            total_count=result.total_count,
            sample_titles=[str(t) for t in titles],
            raw_response=result.raw_response,
            failure_reason=result.failure_reason,
        )

    def acquire(
        self,
        candidate_id: str,
        output_dir: Path,
        html_url: str | None = None,
        pdf_url: str | None = None,
        browser_profile: Path | None = None,
        browser_channel: str = "chromium",
        network_mode: str = "direct",
    ) -> Path | None:
        """DBLP is metadata-only — no PDF acquisition."""
        raise NotImplementedError(
            "DBLP is metadata-only; use publisher links or other providers for PDF"
        )

    def normalize_record(
        self,
        record: dict[str, Any],
        query_id: str,
        rank: int,
        page: int,
        search_expression: str,
    ) -> dict[str, Any]:
        """Convert a DBLP hit into a standard candidate dict.

        DBLP field mapping:
          info.title → title
          info.year → publication_year
          info.authors.author[].text → authors
          info.venue → venue
          info.doi → doi
          info.url → html_url
        """
        info = _extract_info(record)
        dblp_key = _as_text(info.get("key") or record.get("id") or "")
        candidate_id = f"DBLP-{dblp_key}" if dblp_key else f"{query_id}-{rank:04d}"

        venue = _as_text(info.get("venue"))
        venue_url = _as_text(info.get("url", ""))
        content_type = _classify_venue_type(venue_url) if venue_url else ""

        candidate: dict[str, Any] = {
            "artifact_version": 1,
            "candidate_id": candidate_id,
            "source_provider": self.provider_name,
            "query_id": query_id,
            "page": page,
            "rank": rank,
            "search_expression": search_expression,
            "title": _as_text(info.get("title")),
            "abstract": "",  # DBLP does not provide abstracts
            "doi": BaseProvider.normalize_doi(info.get("doi")),
            "venue": venue,
            "content_type": content_type,
            "html_url": venue_url,
            "pdf_url": "",  # DBLP doesn't provide direct PDF links
            "provider_raw": {
                "dblp_key": dblp_key,
                "venue_type": content_type,
            },
        }

        year = _optional_int(info.get("year"))
        if year is not None:
            candidate["publication_year"] = year

        authors = _extract_authors(info)
        if authors:
            candidate["authors"] = authors

        return candidate
