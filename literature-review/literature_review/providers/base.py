"""Abstract provider interface for literature sources."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SearchResult:
    """Provider-agnostic wrapper around one page of search results."""

    provider: str
    query_id: str
    page_number: int
    total_count: int
    records: list[dict[str, Any]]
    """Raw provider records from this page (normalized by pipeline layer)."""
    raw_response: dict[str, Any]
    failure_reason: str | None = None


@dataclass(frozen=True)
class ProbeResult:
    """Lightweight page-1 probe for query evaluation."""

    provider: str
    query_id: str
    total_count: int
    sample_titles: list[str]
    raw_response: dict[str, Any]
    failure_reason: str | None = None


def polite_user_agent() -> str:
    """User-Agent for API etiquette; set LIT_REVIEW_CONTACT to identify yourself."""
    import os

    contact = os.environ.get("LIT_REVIEW_CONTACT", "").strip()
    return f"LiteratureReview/1.0 (mailto:{contact})" if contact else "LiteratureReview/1.0"


class ProviderError(RuntimeError):
    """Base error for provider operations."""

    def __init__(
        self,
        reason: str,
        provider: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(f"[{provider}] {reason}")
        self.reason = reason
        self.provider = provider
        self.details = details or {}


class BaseProvider(ABC):
    """Abstract interface for literature source providers.

    Each provider (IEEE Xplore, arXiv, Semantic Scholar, etc.) implements
    search, probe, and acquire. The pipeline orchestrates through this
    interface without knowing provider-specific HTTP details.
    """

    # Override in subclasses to control per-request delays (seconds).
    # 0 or None means no added delay.
    request_delay: float | None = None

    # Maximum attempts per page in search_paginated (>=1); exponential backoff.
    max_retries: int = 3

    #: HTTP statuses worth retrying (timeouts, rate limits, server errors)
    _TRANSIENT_STATUSES = frozenset({408, 425, 429, 500, 502, 503, 504})

    @classmethod
    def _is_transient(cls, error: Exception) -> bool:
        """Only network-level failures and retryable HTTP statuses qualify.

        Permanent failures (bad API key, malformed query, 4xx other than
        408/425/429) must fail fast instead of burning backoff sleeps.
        """
        status = None
        response = getattr(error, "response", None)  # requests.HTTPError
        if response is not None:
            status = getattr(response, "status_code", None)
        if isinstance(error, ProviderError):
            status = error.details.get("status", status)
        if status is not None:
            return status in cls._TRANSIENT_STATUSES
        return isinstance(error, (TimeoutError, ConnectionError))

    def _search_with_retries(self, *args: Any, **kwargs: Any) -> SearchResult:
        """Call :meth:`search`, retrying transient errors with backoff."""
        attempts = max(1, int(self.max_retries))
        base_delay = self.request_delay or 1.0
        for attempt in range(attempts):
            try:
                return self.search(*args, **kwargs)
            except Exception as error:
                if attempt >= attempts - 1 or not self._is_transient(error):
                    raise
                time.sleep(base_delay * (2 ** attempt))
        raise AssertionError("unreachable")

    def adapt_expression(self, expression: str) -> str:
        """Transform a generic Boolean expression into provider-specific syntax.

        The default is pass-through (IEEE-style Boolean).
        Override for providers with different search syntax (S2, arXiv, DBLP).
        """
        return expression

    def extract_records(self, raw_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract record list from a raw provider response dict.

        Default assumes ``{"records": [...]}`` (IEEE format).
        Override for providers with different envelope keys (e.g. S2 uses ``data``).
        """
        records = raw_data.get("records", raw_data.get("articles"))
        if isinstance(records, list):
            return [r for r in records if isinstance(r, dict)]
        return []

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique provider identifier (e.g. 'ieee_xplore', 'arxiv')."""
        ...

    @abstractmethod
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
        """Execute a single page of metadata search."""
        ...

    def search_paginated(
        self,
        expression: str,
        query_id: str,
        max_pages: int = 5,
        rows_per_page: int = 25,
        delay_seconds: float = 1.0,
        **kwargs: Any,
    ) -> list[SearchResult]:
        """Execute a paginated metadata search across multiple pages.

        Absorbs the pagination loop previously in ieee_web_search.py.
        Stops early when the last page has fewer records than requested.
        """
        results: list[SearchResult] = []
        for page in range(1, max_pages + 1):
            result = self._search_with_retries(
                expression, query_id,
                page_number=page, rows_per_page=rows_per_page,
                **kwargs,
            )
            results.append(result)
            if len(result.records) < rows_per_page:
                break  # last page
            if page < max_pages:
                time.sleep(delay_seconds)
        return results

    @abstractmethod
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
        ...

    @abstractmethod
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
        """Acquire a single paper PDF. Returns Path on success, None on failure."""
        ...

    @abstractmethod
    def normalize_record(
        self,
        record: dict[str, Any],
        query_id: str,
        rank: int,
        page: int,
        search_expression: str,
    ) -> dict[str, Any]:
        """Convert a raw provider record into a standard candidate dict.

        Returns a dict conforming to candidate.schema.json.
        """
        ...

    @staticmethod
    def normalize_doi(value: Any) -> str:
        """Normalize a DOI string across providers."""
        import re

        text = str(value or "").strip().lower()
        return re.sub(
            r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", text
        ).rstrip(" ./")
