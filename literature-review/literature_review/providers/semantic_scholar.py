"""Semantic Scholar provider adapter.

Implements BaseProvider for the Semantic Scholar Academic Graph REST API.
Free tier — no API key required (<100 req/5min). Covers all major CS venues
including ACM, SIAM, Springer, and arXiv preprints.

API docs: https://api.semanticscholar.org/api-docs/graph
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

BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
USER_AGENT = polite_user_agent()

# Fields to request from the API — keep lean for performance
SEARCH_FIELDS = "title,abstract,year,authors,venue,citationCount,externalIds,url,publicationTypes,fieldsOfStudy"

FOS_MAP: dict[str, str] = {
    "Journals": "JournalArticle",
    "Conferences": "Conference",
}


def _as_text(value: Any) -> str:
    return str(value or "").strip()


def _optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _to_list(value: Any) -> list[dict[str, Any]]:
    """Coerce various list-like inputs into a list of dicts."""
    if isinstance(value, list):
        return [v for v in value if isinstance(v, dict)]
    return []


def _build_url(
    expression: str,
    offset: int = 0,
    limit: int = 25,
    year_from: int | None = None,
    year_to: int | None = None,
    content_types: list[str] | None = None,
    sort: str | None = None,
) -> str:
    """Build a Semantic Scholar search URL with query parameters."""
    from urllib.parse import quote, urlencode

    params: dict[str, Any] = {
        "query": expression,
        "offset": offset,
        "limit": limit,
        "fields": SEARCH_FIELDS,
    }

    # Year range via the `year` parameter: e.g. "1970-2026"
    year_parts = []
    if year_from:
        year_parts.append(str(year_from))
    if year_to:
        year_parts.append(str(year_to))
    if year_parts:
        params["year"] = "-".join(year_parts)

    # Content type filter via `publicationTypes`
    pub_types = []
    if content_types:
        for ct in content_types:
            mapped = FOS_MAP.get(ct)
            if mapped:
                pub_types.append(mapped)
    if pub_types:
        params["publicationTypes"] = ",".join(pub_types)

    # Sort — Semantic Scholar supports "relevance" (default), "citationCount:desc", "publicationDate:desc"
    if sort and sort != "relevance":
        params["sort"] = sort

    return f"{BASE_URL}?{urlencode(params, quote_via=quote)}"


def _s2_api_key() -> str | None:
    """Return the Semantic Scholar API key if configured, or None.

    Checks: S2_API_KEY env, LIT_REVIEW_S2_API_KEY env, then
    .env file in project root (key=S2_API_KEY or LITERATURE_REVIEW_S2_API_KEY).
    """
    import os
    from pathlib import Path
    key = os.environ.get("S2_API_KEY") or os.environ.get("LIT_REVIEW_S2_API_KEY")
    if key:
        return key
    # Try reading from .env in project root
    env_file = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            if k.strip() in ("S2_API_KEY", "LITERATURE_REVIEW_S2_API_KEY"):
                return v.strip().strip('"').strip("'")
    return None


def _api_get(url: str, timeout_seconds: int = 30) -> dict[str, Any]:
    """Execute a GET request to the Semantic Scholar API."""
    headers: dict[str, str] = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    api_key = _s2_api_key()
    if api_key:
        headers["x-api-key"] = api_key
    request = Request(url, method="GET", headers=headers)
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            body_text = response.read().decode("utf-8", errors="replace")
    except HTTPError as error:
        body_text = error.read().decode("utf-8", errors="replace")
        if error.code == 429:
            raise ProviderError("rate_limited", "semantic_scholar", {"status": 429}) from error
        raise ProviderError(
            f"http_{error.code}", "semantic_scholar", {"status": error.code},
        ) from error
    except URLError as error:
        raise ProviderError(
            f"network_error: {error.reason}", "semantic_scholar",
        ) from error

    try:
        return json.loads(body_text)
    except json.JSONDecodeError:
        raise ProviderError("non_json_response", "semantic_scholar")


def _extract_total(data: dict[str, Any]) -> int:
    return int(data.get("total", 0) or 0)


def _extract_records(data: dict[str, Any]) -> list[dict[str, Any]]:
    return _to_list(data.get("data"))


def _extract_titles(data: dict[str, Any], limit: int = 5) -> list[str]:
    titles: list[str] = []
    for record in _extract_records(data)[:limit]:
        title = record.get("title")
        if isinstance(title, str) and title.strip():
            titles.append(title.strip())
    return titles


class SemanticScholarProvider(BaseProvider):
    """Semantic Scholar literature source adapter.

    Uses the Academic Graph REST API. An API key is recommended for
    production use (https://api.semanticscholar.org/). Without a key,
    rate limits are very restrictive (~1 req/sec burst).
    """

    request_delay = 1.5   # 1 req/sec S2 policy + safety margin
    max_retries = 3

    def extract_records(self, raw_data: dict[str, Any]) -> list[dict[str, Any]]:
        """S2 uses ``data`` envelope instead of ``records``."""
        data = raw_data.get("data")
        if isinstance(data, list):
            return [r for r in data if isinstance(r, dict)]
        return []

    def adapt_expression(self, expression: str) -> str:
        """Convert generic Boolean to S2 keyword search.

        S2 supports: +term -term "phrase" (no AND/OR/parentheses).
        We extract quoted phrases and meaningful keywords, joining as implicit AND.
        """
        import re
        phrases = re.findall(r'"([^"]+)"', expression)
        cleaned = re.sub(r'\b(AND|OR|NOT)\b', ' ', expression, flags=re.IGNORECASE)
        cleaned = re.sub(r'[()]', ' ', cleaned)
        words = re.findall(r'[a-zA-Z][a-zA-Z0-9*\-]*', cleaned)
        seen: set[str] = set()
        parts: list[str] = []
        for p in phrases:
            key = p.lower()
            if key not in seen:
                parts.append(f'"{p}"')
                seen.add(key)
        for w in words:
            key = w.lower()
            if key not in seen and len(w) > 2:
                parts.append(w)
                seen.add(key)
        return ' '.join(parts)

    @property
    def provider_name(self) -> str:
        return "semantic_scholar"

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
        """Execute a single page of search via Semantic Scholar API.

        Note: S2 uses offset-based pagination, not page numbers.
        We map page_number → offset internally.
        """
        offset = (page_number - 1) * rows_per_page
        url = _build_url(
            expression,
            offset=offset,
            limit=rows_per_page,
            year_from=year_from,
            year_to=year_to,
            content_types=content_types,
            sort=sort,
        )
        try:
            data = _api_get(url, timeout_seconds=timeout_seconds)
            return SearchResult(
                provider=self.provider_name,
                query_id=query_id,
                page_number=page_number,
                total_count=_extract_total(data),
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
            page_number=1, rows_per_page=5,
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
        """PDF acquisition not supported — Semantic Scholar is metadata-only."""
        raise NotImplementedError(
            "Semantic Scholar is metadata-only; use publisher links for PDF acquisition"
        )

    def normalize_record(
        self,
        record: dict[str, Any],
        query_id: str,
        rank: int,
        page: int,
        search_expression: str,
    ) -> dict[str, Any]:
        """Convert a raw Semantic Scholar record into a standard candidate dict.

        S2 field mapping:
          paperId → candidate_id base
          externalIds.DOI → doi
          externalIds.ArXiv → arxiv_id (stored in provider_raw)
          authors[].name → authors
          venue (string) → venue
          year → publication_year
        """
        paper_id = _as_text(record.get("paperId"))
        candidate_id = f"S2-{paper_id}" if paper_id else f"{query_id}-{rank:04d}"

        # Authors
        authors_raw = record.get("authors", [])
        if isinstance(authors_raw, list):
            authors = [
                _as_text(a.get("name") or a.get("authorId"))
                for a in authors_raw
            ]
        else:
            authors = []

        # External IDs
        external = record.get("externalIds") or {}
        doi = BaseProvider.normalize_doi(external.get("DOI") or record.get("doi"))
        arxiv_id = _as_text(external.get("ArXiv"))

        candidate: dict[str, Any] = {
            "artifact_version": 1,
            "candidate_id": candidate_id,
            "source_provider": self.provider_name,
            "query_id": query_id,
            "page": page,
            "rank": rank,
            "search_expression": search_expression,
            "title": _as_text(record.get("title")),
            "abstract": _as_text(record.get("abstract")),
            "doi": doi,
            "venue": _as_text(record.get("venue")),
            "content_type": _as_text(
                record.get("publicationTypes", [None])[0]
                if record.get("publicationTypes") else ""
            ),
            "html_url": _as_text(record.get("url")),
            "pdf_url": "",  # S2 doesn't provide direct PDF links
            "provider_raw": {
                "paper_id": paper_id,
                "arxiv_id": arxiv_id,
            },
        }

        year = _optional_int(record.get("year"))
        citation_count = _optional_int(record.get("citationCount"))

        if year is not None:
            candidate["publication_year"] = year
        if citation_count is not None:
            candidate["citation_count"] = citation_count
        if authors:
            candidate["authors"] = authors

        # Fields of study → keywords (can be list of dicts or list of strings)
        fos = record.get("fieldsOfStudy") or record.get("s2FieldsOfStudy")
        if isinstance(fos, list) and fos:
            keywords = []
            for f in fos:
                if isinstance(f, dict):
                    kw = _as_text(f.get("category") or f.get("name") or "")
                else:
                    kw = _as_text(f)
                if kw:
                    keywords.append(kw)
            if keywords:
                candidate["keywords"] = keywords

        return candidate
