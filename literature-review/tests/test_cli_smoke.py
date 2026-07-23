"""Smoke tests for the v2 package."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_cli_version():
    r = subprocess.run([sys.executable, "-m", "literature_review.cli", "--version"],
                       capture_output=True, text=True)
    assert r.returncode == 0
    assert "Literature Review" in r.stdout


def test_cli_help():
    r = subprocess.run([sys.executable, "-m", "literature_review.cli", "--help"],
                       capture_output=True, text=True)
    assert r.returncode == 0


def test_lit_review_entry_point():
    r = subprocess.run(["lit-review", "--version"], capture_output=True, text=True)
    assert r.returncode == 0


def test_provider_import():
    from literature_review.providers.base import BaseProvider, ProbeResult, ProviderError, SearchResult
    from literature_review.providers.ieee import IeeeXploreProvider
    assert issubclass(IeeeXploreProvider, BaseProvider)
    p = IeeeXploreProvider()
    assert p.provider_name == "ieee_xplore"


def test_normalize_doi():
    from literature_review.providers.base import BaseProvider
    assert BaseProvider.normalize_doi("10.1109/TPEL.2024") == "10.1109/tpel.2024"
    assert BaseProvider.normalize_doi("https://doi.org/10.1109/TPEL.2024") == "10.1109/tpel.2024"
    assert BaseProvider.normalize_doi("") == ""
    assert BaseProvider.normalize_doi(None) == ""


def test_ieee_normalize_record():
    from literature_review.providers.ieee import IeeeXploreProvider
    p = IeeeXploreProvider()
    raw = {"articleNumber": "1234567", "articleTitle": "Test LLC",
           "doi": "10.1109/TPEL.2024.99", "publicationYear": "2024",
           "publicationTitle": "IEEE Trans.", "contentType": "Journals",
           "htmlLink": "/doc/123", "abstract": "test", "citationCount": "15"}
    c = p.normalize_record(raw, "Q1", 1, 1, '("LLC")')
    assert c["candidate_id"] == "IEEE-1234567"
    assert c["title"] == "Test LLC"
    assert c["publication_year"] == 2024


def test_ieee_acquire_stub():
    import pytest
    from literature_review.providers.ieee import IeeeXploreProvider
    p = IeeeXploreProvider()
    with pytest.raises(NotImplementedError):
        p.acquire("C001", Path("/tmp"))


def test_sha256_stability(sample_brief):
    from literature_review.pipeline.brief import scope_sha256
    h1 = scope_sha256(sample_brief)
    h2 = scope_sha256(dict(sample_brief))
    assert h1 == h2
    assert len(h1) == 64


def test_sha256_sensitivity(sample_brief):
    from literature_review.pipeline.brief import scope_sha256
    h1 = scope_sha256(sample_brief)
    m = dict(sample_brief)
    m["research_objective"] = "Different"
    assert scope_sha256(m) != h1
