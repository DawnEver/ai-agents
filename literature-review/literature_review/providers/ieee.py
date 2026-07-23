"""IEEE Xplore provider adapter.

Implements BaseProvider for the IEEE Xplore REST search API.
All IEEE-specific HTTP and record-normalization logic is self-contained here —
the single source of truth, absorbing scripts/ieee_web_client.py,
scripts/normalize_candidates.py, and scripts/ieee_web_probe.py helpers.
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
)

DEFAULT_SEARCH_URL = "https://ieeexplore.ieee.org/rest/search"
IEEE_BASE_URL = "https://ieeexplore.ieee.org"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


# ---------------------------------------------------------------------------
# Internal helpers (absorbed from scripts/ieee_web_client.py)
# ---------------------------------------------------------------------------

def _as_text(value: Any) -> str:
    return str(value or "").strip()


def _optional_int(value: Any) -> int | None:
    text = _as_text(value)
    return int(text) if text.isdigit() else None


def _absolute_ieee_url(value: Any) -> str:
    text = _as_text(value)
    if not text:
        return ""
    if text.startswith("http://") or text.startswith("https://"):
        return text
    if not text.startswith("/"):
        text = "/" + text
    return IEEE_BASE_URL + text


def _classify_failure(status: int, body_text: str, content_type: str) -> str | None:
    """Classify an IEEE response as success or a specific failure reason."""
    lowered_body = body_text.lower()
    lowered_type = content_type.lower()

    if status == 403:
        return "http_403"
    if status == 429:
        return "http_429"
    if status >= 400:
        return f"http_{status}"

    # Search results can legitimately contain words such as "both" or "robotics".
    # A structurally valid search payload is not an access-control challenge.
    if "json" in lowered_type:
        try:
            parsed = json.loads(body_text)
        except json.JSONDecodeError:
            pass
        else:
            if isinstance(parsed, dict) and (
                "records" in parsed or "totalRecords" in parsed or "breadCrumbs" in parsed
            ):
                return None

    if (
        "captcha" in lowered_body
        or "robot check" in lowered_body
        or "bot check" in lowered_body
        or "verify you are human" in lowered_body
    ):
        return "captcha_or_bot_check"
    if "sign in" in lowered_body or "login" in lowered_body or "institutional sign" in lowered_body:
        return "login_required"
    if "json" not in lowered_type:
        return "non_json_response"
    return None


def _build_search_payload(
    expression: str,
    page_number: int = 1,
    rows_per_page: int = 25,
    search_field: str = "All Metadata",
    year_from: int | None = None,
    year_to: int | None = None,
    content_types: list[str] | None = None,
    sort: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "queryText": expression,
        "newsearch": True,
        "pageNumber": page_number,
        "rowsPerPage": rows_per_page,
    }
    if search_field:
        payload["searchField"] = search_field
    if year_from is not None and year_to is not None:
        payload["ranges"] = [f"{year_from}_{year_to}_Year"]
    if content_types:
        payload["refinements"] = [f"ContentType:{value}" for value in content_types]
    if sort:
        payload["sortType"] = sort
    return payload


def _post_search(
    expression: str,
    base_url: str = DEFAULT_SEARCH_URL,
    page_number: int = 1,
    rows_per_page: int = 25,
    timeout_seconds: int = 30,
    *,
    search_scope: str = "metadata",
    year_from: int | None = None,
    year_to: int | None = None,
    content_types: list[str] | None = None,
    sort: str | None = None,
) -> dict[str, Any]:
    """Execute a single IEEE Xplore REST search POST.  Returns parsed JSON dict."""
    search_field = "Abstract" if search_scope == "abstract" else "All Metadata"
    payload = _build_search_payload(
        expression, page_number, rows_per_page, search_field,
        year_from, year_to, content_types, sort,
    )
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        base_url,
        data=body,
        method="POST",
        headers={
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Referer": "https://ieeexplore.ieee.org/search/searchresult.jsp",
            "Origin": "https://ieeexplore.ieee.org",
        },
    )

    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            body_text = response.read().decode("utf-8", errors="replace")
            content_type = response.headers.get("content-type", "")
    except HTTPError as error:
        body_text = error.read().decode("utf-8", errors="replace")
        content_type = error.headers.get("content-type", "")
        failure = _classify_failure(error.code, body_text, content_type)
        raise ProviderError(
            failure or f"http_{error.code}", "ieee_xplore",
            {"status": error.code},
        ) from error
    except URLError as error:
        raise ProviderError(
            f"network_error: {error.reason}", "ieee_xplore",
        ) from error

    failure = _classify_failure(200, body_text, content_type)
    if failure:
        raise ProviderError(failure, "ieee_xplore")

    try:
        data = json.loads(body_text)
    except json.JSONDecodeError:
        raise ProviderError("non_json_response", "ieee_xplore")

    if not isinstance(data, dict):
        raise ProviderError("unexpected_json_shape", "ieee_xplore")
    return data


def _extract_records(data: dict[str, Any]) -> list[dict[str, Any]]:
    records = data.get("records") or data.get("articles") or []
    return records if isinstance(records, list) else []


def _extract_total_count(data: dict[str, Any]) -> int:
    for key in ("totalRecords", "total", "totalfound"):
        value = data.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return len(_extract_records(data))


def _extract_titles(data: dict[str, Any], limit: int = 5) -> list[str]:
    titles: list[str] = []
    for record in _extract_records(data)[:limit]:
        if not isinstance(record, dict):
            continue
        title = record.get("articleTitle") or record.get("title")
        if isinstance(title, str) and title.strip():
            titles.append(title.strip())
    return titles


def _extract_search_expression(data: dict[str, Any]) -> str:
    for crumb in data.get("breadCrumbs", []):
        for child in crumb.get("children", []):
            value = child.get("value") or child.get("reference")
            if value:
                return _as_text(value)
    return ""


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------

class IeeeXploreProvider(BaseProvider):
    """IEEE Xplore literature source adapter.

    Uses the IEEE Xplore REST search API for metadata search and probe.
    PDF acquisition is handled externally via the browser/ module.
    """

    @property
    def provider_name(self) -> str:
        return "ieee_xplore"

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
        search_scope: str = "metadata",
    ) -> SearchResult:
        """Execute a single page of metadata search via IEEE REST API.

        Records are returned as raw dicts — normalization is the caller's
        responsibility (typically performed by the pipeline layer, not by
        the provider itself).
        """
        try:
            data = _post_search(
                expression,
                page_number=page_number,
                rows_per_page=rows_per_page,
                timeout_seconds=timeout_seconds,
                search_scope=search_scope,
                year_from=year_from,
                year_to=year_to,
                content_types=content_types,
                sort=sort,
            )
            return SearchResult(
                provider=self.provider_name,
                query_id=query_id,
                page_number=page_number,
                total_count=_extract_total_count(data),
                records=_extract_records(data),
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
        """Probe page 1 to estimate result count and relevance."""
        result = self.search(
            expression, query_id,
            page_number=1, rows_per_page=25,
            year_from=year_from, year_to=year_to,
            content_types=content_types, sort=sort,
            timeout_seconds=timeout_seconds,
        )
        return ProbeResult(
            provider=self.provider_name,
            query_id=query_id,
            total_count=result.total_count,
            sample_titles=_extract_titles(result.raw_response),
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
        """PDF acquisition stub — implemented via browser/ module."""
        raise NotImplementedError(
            "PDF acquisition uses browser/ module, not provider"
        )

    def normalize_record(
        self,
        record: dict[str, Any],
        query_id: str,
        rank: int,
        page: int,
        search_expression: str,
    ) -> dict[str, Any]:
        """Convert a raw IEEE record into a standard candidate dict.

        Absorbed from scripts/normalize_candidates.py: IEEE field mapping —
        articleTitle→title, publicationTitle→venue, htmlLink→html_url, etc.
        """
        article_number = _as_text(record.get("articleNumber") or record.get("arnumber"))
        candidate_id = (
            f"IEEE-{article_number}" if article_number else f"{query_id}-{rank:04d}"
        )

        candidate: dict[str, Any] = {
            "artifact_version": 1,
            "candidate_id": candidate_id,
            "source_provider": self.provider_name,
            "query_id": query_id,
            "page": page,
            "rank": rank,
            "search_expression": search_expression,
            "title": _as_text(
                record.get("articleTitle")
                or record.get("title")
                or record.get("highlightedTitle")
            ),
            "abstract": _as_text(
                record.get("abstract") or record.get("abstractText")
            ),
            "doi": BaseProvider.normalize_doi(record.get("doi")),
            "venue": _as_text(
                record.get("publicationTitle")
                or record.get("displayPublicationTitle")
            ),
            "content_type": _as_text(
                record.get("contentType") or record.get("articleContentType")
            ),
            "html_url": _absolute_ieee_url(
                record.get("htmlLink") or record.get("documentLink")
            ),
            "pdf_url": _absolute_ieee_url(record.get("pdfLink")),
            "provider_raw": {
                "article_number": article_number,
            },
        }

        publication_year = _optional_int(record.get("publicationYear"))
        citation_count = _optional_int(record.get("citationCount"))

        if publication_year is not None:
            candidate["publication_year"] = publication_year
        if citation_count is not None:
            candidate["citation_count"] = citation_count

        # Authors — IEEE returns authors as a nested structure
        authors_raw = record.get("authors")
        if isinstance(authors_raw, list):
            candidate["authors"] = [
                _as_text(a.get("name") or a.get("preferredName") or str(a))
                for a in authors_raw
            ]

        return candidate
