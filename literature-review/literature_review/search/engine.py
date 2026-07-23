"""Search orchestration — probe, search, dedupe, and multi-provider discovery.

This module exposes the core search pipeline primitives.  The heavy
implementations live in ``literature_review.pipeline.search``; this module
adds a higher-level ``search_all_providers`` entrypoint and re-exports the
preserved functions for convenience.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from literature_review.models import Candidate, QueryPlan
from literature_review.pipeline.search import (  # noqa: F401 — re-export
    get_provider,
    run_dedupe_rank,
    run_probe,
    run_search,
)


def search_all_providers(
    plan: QueryPlan,
    providers: list[str],
    max_pages: int = 5,
    rows_per_page: int = 25,
    delay_seconds: float = 1.0,
    timeout_seconds: int = 30,
) -> list[Candidate]:
    """Search every enabled query across all matching *providers*.

    For each :class:`QueryItem` in *plan* whose ``enabled`` flag is set and
    ``expression`` is non-empty, the matching provider(s) execute a paginated
    metadata search.  Results are normalised and returned as a flat list of
    :class:`Candidate` objects — ready for deduplication and screening.

    Parameters
    ----------
    plan:
        Query plan carrying the list of enabled query items.
    providers:
        Available provider names (e.g. ``["ieee_xplore"]``).
    max_pages:
        Maximum pages to fetch per query.
    rows_per_page:
        Records requested per page.
    delay_seconds:
        Inter-page delay to respect rate limits.
    timeout_seconds:
        Per-request HTTP timeout.
    """
    candidates: list[Candidate] = []

    for query in plan.queries:
        if not query.enabled or not query.expression:
            continue

        # Resolve the provider(s) for this query item
        target = [query.provider] if query.provider else providers

        for name in target:
            if name not in providers:
                continue

            try:
                prov = get_provider(name)
            except ValueError:
                continue

            try:
                results = prov.search_paginated(
                    expression=query.expression,
                    query_id=query.query_id,
                    max_pages=max_pages,
                    rows_per_page=rows_per_page,
                    delay_seconds=delay_seconds,
                    timeout_seconds=timeout_seconds,
                    year_from=query.year_from,
                    year_to=query.year_to,
                    content_types=query.content_types,
                    sort=query.sort,
                )
            except Exception:
                continue

            for result in results:
                if result.failure_reason:
                    continue

                for position, record in enumerate(result.records, start=1):
                    if not isinstance(record, dict):
                        continue

                    rank = (result.page_number - 1) * rows_per_page + position
                    normalised = prov.normalize_record(
                        record,
                        query_id=query.query_id,
                        rank=rank,
                        page=result.page_number,
                        search_expression=query.expression,
                    )

                    candidates.append(
                        Candidate(
                            candidate_id=str(normalised.get("candidate_id", "")),
                            source_provider=name,
                            title=str(normalised.get("title", "")),
                            abstract=str(normalised.get("abstract", "")),
                            doi=str(normalised.get("doi", "")),
                            authors=normalised.get("authors") or [],
                            venue=str(normalised.get("venue", "")),
                            publication_year=_int_or_none(
                                normalised.get("publication_year")
                            ),
                            content_type=str(normalised.get("content_type", "")),
                            keywords=normalised.get("keywords") or [],
                            citation_count=int(
                                normalised.get("citation_count") or 0
                            ),
                            html_url=str(normalised.get("html_url", "")),
                            pdf_url=str(normalised.get("pdf_url", "")),
                            provider_raw=record,
                            query_id=query.query_id,
                            page=result.page_number,
                            rank=rank,
                            search_expression=query.expression,
                        )
                    )

    return candidates


def _int_or_none(value: object) -> int | None:
    """Cast *value* to int or return None."""
    if value is None:
        return None
    try:
        return int(value)  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return None
