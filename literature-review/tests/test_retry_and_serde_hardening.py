"""Regression tests for sharp-review round 2 (SR-007..022)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from literature_review.providers.base import BaseProvider, ProbeResult, ProviderError, SearchResult


class RetryProbe(BaseProvider):
    """Provider whose search raises a scripted sequence of exceptions."""

    def __init__(self, script: list[Exception | None]):
        self._script = list(script)
        self.calls = 0

    @property
    def provider_name(self) -> str:
        return "retry_probe"

    def search(self, expression, query_id, page_number=1, rows_per_page=25, **kwargs) -> SearchResult:
        self.calls += 1
        step = self._script.pop(0) if self._script else None
        if step is not None:
            raise step
        return SearchResult(provider="retry_probe", query_id=query_id, page_number=page_number,
                            total_count=1, records=[{"id": 1}], raw_response={})

    def probe(self, expression, query_id, **kwargs) -> ProbeResult:
        raise NotImplementedError

    def acquire(self, candidate_id, output_dir, **kwargs) -> Path | None:
        return None

    def normalize_record(self, record, query_id, rank, page, search_expression) -> dict[str, Any]:
        return dict(record)


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    import literature_review.providers.base as base_mod
    monkeypatch.setattr(base_mod.time, "sleep", lambda s: None)


def test_transient_errors_are_retried():
    prov = RetryProbe([ConnectionError("reset"), TimeoutError("slow"), None])
    results = prov.search_paginated("x", "q1", max_pages=1)
    assert prov.calls == 3
    assert results[0].records == [{"id": 1}]


def test_permanent_errors_fail_fast():
    prov = RetryProbe([ValueError("malformed query"), None])
    with pytest.raises(ValueError):
        prov.search_paginated("x", "q1", max_pages=1)
    assert prov.calls == 1, "permanent failures must not be retried"


def test_provider_error_with_transient_status_is_retried():
    err = ProviderError("rate limited", "retry_probe", details={"status": 429})
    prov = RetryProbe([err, None])
    results = prov.search_paginated("x", "q1", max_pages=1)
    assert prov.calls == 2
    assert results[0].total_count == 1


def test_provider_error_with_permanent_status_fails_fast():
    err = ProviderError("bad key", "retry_probe", details={"status": 403})
    prov = RetryProbe([err, None])
    with pytest.raises(ProviderError):
        prov.search_paginated("x", "q1", max_pages=1)
    assert prov.calls == 1


# ---------------------------------------------------------------------------
# Serde hardening
# ---------------------------------------------------------------------------

def test_from_dict_missing_required_field_raises_clear_error():
    from literature_review.models import Candidate

    with pytest.raises(ValueError, match="Candidate.*candidate_id"):
        Candidate.from_dict({"title": "T", "source_provider": "x"})


def test_run_stats_skips_malformed_rows(tmp_path, monkeypatch):
    """One bad candidate row must not abort plotting (SR-011)."""
    from literature_review.pipeline import orchestrator

    td = tmp_path / "t"
    (td / "search").mkdir(parents=True)
    rows = [
        {"candidate_id": "a", "source_provider": "p", "title": "A", "publication_year": 2024},
        {"title": "missing required ids"},  # malformed
    ]
    (td / "search" / "candidates_ranked.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8",
    )

    seen: dict[str, int] = {}
    monkeypatch.setattr(orchestrator, "_plot_candidates", None, raising=False)
    import literature_review.export.plot as plot_mod
    monkeypatch.setattr(plot_mod, "plot_year_distribution", lambda cands, p: seen.update(n=len(cands)))
    monkeypatch.setattr(plot_mod, "plot_venue_distribution", lambda cands, p: None)

    stats = orchestrator.run_stats(td, plots=True)
    assert "plot_error" not in stats
    assert seen["n"] == 1, "good rows must survive a bad sibling"
