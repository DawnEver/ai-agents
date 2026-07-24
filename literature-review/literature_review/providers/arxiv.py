"""arXiv provider adapter.

Implements BaseProvider for the arXiv REST API.
Free — no API key required. Covers CS theory preprints:
cs.DM, cs.DS, cs.CC, cs.AI, math.CO, and more.

API docs: https://info.arxiv.org/help/api/user-manual.html
Rate limit: one request per 3 seconds (polite delay).
"""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
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

BASE_URL = "http://export.arxiv.org/api/query"
USER_AGENT = polite_user_agent()

# arXiv API namespace
ARXIV_NS = "http://www.w3.org/2005/Atom"
OPENSEARCH_NS = "http://a9.com/-/spec/opensearch/1.1/"
ARXIV_NS_SHORT = "http://arxiv.org/schemas/atom"


def _as_text(value: Any) -> str:
    return str(value or "").strip()


def _optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _build_url(
    expression: str,
    start: int = 0,
    max_results: int = 25,
    sort: str | None = None,
) -> str:
    """Build an arXiv API query URL."""
    from urllib.parse import quote, urlencode

    params: dict[str, Any] = {
        "search_query": expression,
        "start": start,
        "max_results": max_results,
    }
    if sort == "relevance":
        params["sortBy"] = "relevance"
        params["sortOrder"] = "descending"
    elif sort == "date" or sort == "publicationDate:desc":
        params["sortBy"] = "submittedDate"
        params["sortOrder"] = "descending"

    return f"{BASE_URL}?{urlencode(params, quote_via=quote)}"


def _api_get(url: str, timeout_seconds: int = 30) -> str:
    """Execute a GET request to the arXiv API. Returns raw XML text."""
    request = Request(
        url,
        method="GET",
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/atom+xml",
        },
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return response.read().decode("utf-8", errors="replace")
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        if error.code == 429:
            raise ProviderError("rate_limited", "arxiv", {"status": 429}) from error
        raise ProviderError(
            f"http_{error.code}", "arxiv", {"status": error.code},
        ) from error
    except URLError as error:
        raise ProviderError(
            f"network_error: {error.reason}", "arxiv",
        ) from error


def _parse_atom(xml_text: str) -> dict[str, Any]:
    """Parse arXiv Atom XML response into a dict with total_count and records."""
    root = ET.fromstring(xml_text)

    # Total count from opensearch
    total = 0
    for elem in root:
        if elem.tag.endswith("}totalResults"):
            total = int(elem.text or "0")
            break

    records: list[dict[str, Any]] = []
    for entry in root.findall(f"{{{ARXIV_NS}}}entry"):
        record: dict[str, Any] = {}

        # Title
        title_elem = entry.find(f"{{{ARXIV_NS}}}title")
        record["title"] = _as_text(title_elem.text) if title_elem is not None else ""

        # Summary (abstract)
        summary_elem = entry.find(f"{{{ARXIV_NS}}}summary")
        record["abstract"] = _as_text(summary_elem.text) if summary_elem is not None else ""

        # Published date
        published = entry.find(f"{{{ARXIV_NS}}}published")
        year = None
        if published is not None and published.text:
            m = re.match(r"(\d{4})", published.text.strip())
            if m:
                year = int(m.group(1))
        record["year"] = year

        # Authors
        authors = []
        for author_elem in entry.findall(f"{{{ARXIV_NS}}}author"):
            name_elem = author_elem.find(f"{{{ARXIV_NS}}}name")
            if name_elem is not None and name_elem.text:
                authors.append(name_elem.text.strip())
        record["authors"] = authors

        # IDs — extract arxiv ID from the <id> tag
        id_elem = entry.find(f"{{{ARXIV_NS}}}id")
        arxiv_id = ""
        if id_elem is not None and id_elem.text:
            # e.g. "http://arxiv.org/abs/1005.5449v1" → "1005.5449"
            arxiv_url = id_elem.text.strip()
            m = re.search(r"arxiv\.org/abs/([^v]+)", arxiv_url)
            if m:
                arxiv_id = m.group(1)
        record["arxiv_id"] = arxiv_id

        # DOI
        doi = ""
        for link_elem in entry.findall(f"{{{ARXIV_NS}}}link"):
            href = link_elem.get("href", "")
            title_attr = link_elem.get("title", "")
            if "doi" in title_attr.lower() or "doi" in href.lower():
                doi_match = re.search(r"10\.\d{4,}/[^\s]+", href)
                if doi_match:
                    doi = doi_match.group(0)
                break
        record["doi"] = doi

        # URL
        record["html_url"] = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else ""
        record["pdf_url"] = f"https://arxiv.org/pdf/{arxiv_id}" if arxiv_id else ""

        # Categories → keywords
        categories = []
        for cat_elem in entry.findall(f"{{{ARXIV_NS}}}category"):
            term = cat_elem.get("term", "")
            if term:
                categories.append(term)
        record["keywords"] = categories

        # Primary category → venue hint
        primary_cat = ""
        for cat_elem in entry.findall(f"{{{ARXIV_NS_SHORT}}}primary_category"):
            primary_cat = cat_elem.get("term", "")
            break
        record["primary_category"] = primary_cat
        record["venue"] = f"arXiv:{primary_cat}" if primary_cat else "arXiv"

        records.append(record)

    return {"total_count": total, "records": records}


class ArxivProvider(BaseProvider):
    """arXiv literature source adapter.

    Uses the free arXiv REST API (Atom XML). No authentication required.
    Best for CS theory preprints across cs.DM, cs.DS, cs.CC, math.CO.
    """

    # arXiv API etiquette: no more than one request every 3 seconds
    request_delay = 3.0

    @property
    def provider_name(self) -> str:
        return "arxiv"

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
        """Execute a single page of search via arXiv API.

        Note: arXiv uses start-index pagination, not page numbers.
        Year range is appended to the query expression (arXiv API limitation).
        """
        # arXiv API doesn't support year filter natively — append to query
        full_expr = expression
        if year_from and year_to:
            full_expr += f" AND submittedDate:[{year_from}01010000 TO {year_to}12312359]"

        start = (page_number - 1) * rows_per_page
        url = _build_url(full_expr, start=start, max_results=rows_per_page, sort=sort)

        try:
            xml_text = _api_get(url, timeout_seconds=timeout_seconds)
            parsed = _parse_atom(xml_text)
            return SearchResult(
                provider=self.provider_name,
                query_id=query_id,
                page_number=page_number,
                total_count=parsed["total_count"],
                records=parsed["records"],
                raw_response={"xml_length": len(xml_text)},
            )
        except ProviderError:
            raise
        except ET.ParseError as exc:
            raise ProviderError(f"xml_parse_error: {exc}", self.provider_name) from exc
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
        """Probe page 1 with max_results=3 for a quick estimate."""
        result = self.search(
            expression, query_id,
            page_number=1, rows_per_page=3,
            year_from=year_from, year_to=year_to,
            content_types=content_types, sort=sort,
            timeout_seconds=timeout_seconds,
        )
        titles = [
            str(r.get("title", ""))
            for r in result.records[:5]
            if r.get("title")
        ]
        return ProbeResult(
            provider=self.provider_name,
            query_id=query_id,
            total_count=result.total_count,
            sample_titles=titles,
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
        """arXiv PDFs can be downloaded directly via HTTP. Stub for now."""
        raise NotImplementedError(
            "arXiv PDF acquisition not yet implemented; use pdf_url directly"
        )

    def normalize_record(
        self,
        record: dict[str, Any],
        query_id: str,
        rank: int,
        page: int,
        search_expression: str,
    ) -> dict[str, Any]:
        """Convert a parsed arXiv Atom entry into a standard candidate dict.

        Uses the pre-parsed dict from _parse_atom() rather than raw XML.
        """
        arxiv_id = _as_text(record.get("arxiv_id"))
        candidate_id = f"arXiv-{arxiv_id}" if arxiv_id else f"{query_id}-{rank:04d}"

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
            "doi": BaseProvider.normalize_doi(record.get("doi")),
            "venue": _as_text(record.get("venue")),
            "content_type": "preprint",
            "html_url": _as_text(record.get("html_url")),
            "pdf_url": _as_text(record.get("pdf_url")),
            "provider_raw": {
                "arxiv_id": arxiv_id,
                "primary_category": _as_text(record.get("primary_category")),
            },
        }

        year = _optional_int(record.get("year"))
        if year is not None:
            candidate["publication_year"] = year

        authors = record.get("authors")
        if isinstance(authors, list) and authors:
            candidate["authors"] = authors

        keywords = record.get("keywords")
        if isinstance(keywords, list) and keywords:
            candidate["keywords"] = keywords

        return candidate
