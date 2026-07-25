"""Coverage for the queue / match / manifest stage and its orchestrator wiring.

This module had zero tests, which is why the match-report path drifted out of
sync with the orchestrator and silently disabled manifest generation.
"""

from __future__ import annotations

import json

import pytest

from literature_review.pipeline.acquire import (
    approve_download_queue,
    match_pdfs,
    validate_pdf,
    write_download_manifest,
    write_download_queue,
)

# A minimal but real PDF: header, one object, trailer. Must exceed MIN_PDF_BYTES.
PDF_BYTES = b"%PDF-1.4\n" + b"%padding\n" * 200 + b"trailer\n%%EOF\n"


def _screening_row(cid, decision="include", **extra):
    row = {
        "candidate_id": cid,
        "title": f"Paper {cid}",
        "decision": decision,
        "download_priority": "high",
        "doi": f"10.1000/{cid}",
        "html_url": f"https://example.org/{cid}",
        "pdf_url": "",
        "inclusion_reasons": ["relevant"],
        "exclusion_reasons": [],
        "uncertainties": [],
        "publication_year": 2024,
        "publication_title": "Journal of Testing",
    }
    row.update(extra)
    return row


@pytest.fixture
def workspace(tmp_path):
    (tmp_path / "screening").mkdir()
    return tmp_path


def _write_screening(workspace, rows):
    path = workspace / "screening" / "screening_stage1.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Queue construction
# ---------------------------------------------------------------------------

def test_queue_includes_include_and_maybe_decisions(workspace):
    screening = _write_screening(workspace, [
        _screening_row("a", "include"),
        _screening_row("b", "maybe"),
        _screening_row("c", "exclude"),
    ])
    write_download_queue(screening, workspace / "download")

    queue = json.loads((workspace / "download" / "download_queue.json").read_text(encoding="utf-8"))
    assert {i["candidate_id"] for i in queue["items"]} == {"a", "b"}


def test_queue_skips_download_priority_none(workspace):
    screening = _write_screening(workspace, [_screening_row("a", download_priority="none")])
    write_download_queue(screening, workspace / "download")

    queue = json.loads((workspace / "download" / "download_queue.json").read_text(encoding="utf-8"))
    assert queue["items"] == []


def test_queue_items_start_unapproved_and_carry_urls(workspace):
    screening = _write_screening(workspace, [_screening_row("a")])
    write_download_queue(screening, workspace / "download")

    item = json.loads((workspace / "download" / "download_queue.json").read_text(encoding="utf-8"))["items"][0]
    assert item["approved"] is False
    assert item["doi"] == "10.1000/a"
    assert item["html_url"] == "https://example.org/a"


def test_approve_marks_only_named_candidates(workspace):
    screening = _write_screening(workspace, [_screening_row("a"), _screening_row("b")])
    write_download_queue(screening, workspace / "download")
    queue_path = workspace / "download" / "download_queue.json"

    approve_download_queue(queue_path, ["a"], "tester")

    items = {i["candidate_id"]: i for i in json.loads(queue_path.read_text(encoding="utf-8"))["items"]}
    assert items["a"]["approved"] is True
    assert items["b"]["approved"] is False


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------

def _approved_queue(workspace, cids):
    screening = _write_screening(workspace, [_screening_row(c) for c in cids])
    write_download_queue(screening, workspace / "download")
    queue_path = workspace / "download" / "download_queue.json"
    approve_download_queue(queue_path, list(cids), "tester")
    return queue_path


def test_match_pdfs_reports_its_own_output_path(workspace):
    """The orchestrator must not have to guess where the report landed."""
    queue_path = _approved_queue(workspace, ["a"])
    (workspace / "pdfs").mkdir()
    (workspace / "pdfs" / "a_Paper a.pdf").write_bytes(PDF_BYTES)

    result = match_pdfs(queue_path, workspace)

    assert "report_path" in result
    from pathlib import Path
    assert Path(result["report_path"]).exists()


def test_match_pdfs_matches_by_candidate_id_in_filename(workspace):
    queue_path = _approved_queue(workspace, ["a"])
    (workspace / "pdfs").mkdir()
    (workspace / "pdfs" / "a_Paper a.pdf").write_bytes(PDF_BYTES)

    result = match_pdfs(queue_path, workspace)

    assert result["matched_count"] == 1


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

def test_manifest_is_written_from_match_report(workspace):
    queue_path = _approved_queue(workspace, ["a"])
    (workspace / "pdfs").mkdir()
    (workspace / "pdfs" / "a_Paper a.pdf").write_bytes(PDF_BYTES)
    result = match_pdfs(queue_path, workspace)

    from pathlib import Path
    count = write_download_manifest(Path(result["report_path"]), workspace / "handoff")

    manifest = json.loads((workspace / "handoff" / "download_manifest.json").read_text(encoding="utf-8"))
    assert count == 1
    assert manifest["papers"][0]["candidate_id"] == "a"


# ---------------------------------------------------------------------------
# PDF validation must mean one thing across the codebase
# ---------------------------------------------------------------------------

def test_validate_pdf_rejects_truncated_stub(tmp_path):
    """A 300-byte stub must not pass download and then fail at manifest time."""
    from literature_review.acquire.download import validate_pdf as download_validate

    stub = tmp_path / "stub.pdf"
    stub.write_bytes(b"%PDF-1.4\n" + b"x" * 100)

    with pytest.raises(ValueError):
        validate_pdf(stub)
    with pytest.raises(ValueError):
        download_validate(stub)


def test_validate_pdf_accepts_a_real_pdf(tmp_path):
    from literature_review.acquire.download import validate_pdf as download_validate

    good = tmp_path / "good.pdf"
    good.write_bytes(PDF_BYTES)

    validate_pdf(good)
    download_validate(good)


# ---------------------------------------------------------------------------
# Orchestrator wiring — the regression that disabled ingest
# ---------------------------------------------------------------------------

def test_run_acquire_produces_a_manifest(workspace, monkeypatch):
    """End-to-end: a successful download must yield handoff/download_manifest.json."""
    from literature_review.pipeline import orchestrator

    _write_screening(workspace, [_screening_row("a")])

    def fake_acquire_pdfs(queue_path, run_dir, **kwargs):
        pdf_dir = run_dir / "pdfs"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        (pdf_dir / "a_Paper a.pdf").write_bytes(PDF_BYTES)
        return [{"candidate_id": "a", "status": "downloaded"}]

    monkeypatch.setattr(
        "literature_review.acquire.download.acquire_pdfs", fake_acquire_pdfs
    )

    result = orchestrator.run_acquire(workspace, approved_by="tester")

    assert result["manifest_path"] is not None
    assert (workspace / "handoff" / "download_manifest.json").exists()
