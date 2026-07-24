"""Regression tests for arXiv Atom parsing (sharp-review SR-20260724-001)."""

from __future__ import annotations

from literature_review.providers.arxiv import ArxivProvider, _parse_atom

_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <opensearch:totalResults>1</opensearch:totalResults>
  <entry>
    <id>http://arxiv.org/abs/2401.01234v1</id>
    <title>LLC Converter Study</title>
    <summary>An abstract.</summary>
    <published>2024-01-05T00:00:00Z</published>
    <author><name>Wei Zhang</name></author>
    <link href="http://arxiv.org/abs/2401.01234v1" rel="alternate" type="text/html"/>
    <link href="http://arxiv.org/pdf/2401.01234v1" rel="related" type="application/pdf" title="pdf"/>
    <category term="eess.SY"/>
    <arxiv:primary_category term="eess.SY"/>
  </entry>
</feed>
"""


def test_parse_atom_extracts_entries():
    parsed = _parse_atom(_ATOM)
    records = parsed["records"]
    assert len(records) == 1, "namespace must match real arXiv Atom feeds"
    rec = records[0]
    assert rec["title"] == "LLC Converter Study"
    assert rec["authors"] == ["Wei Zhang"]
    assert "eess.SY" in rec.get("categories", []) or rec.get("primary_category") == "eess.SY"


def test_arxiv_provider_declares_polite_delay():
    assert (ArxivProvider().request_delay or 0) >= 3.0
