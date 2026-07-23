"""Screening operations — packet creation and agent-screening import."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

FORBIDDEN_FIELDS = {"local_pdf_path", "pdf_path", "pdf_sha256", "full_text", "pdf_text"}

DECISIONS = {"include", "maybe", "exclude"}
PRIORITIES = {"none", "low", "medium", "high"}
LIST_FIELDS = ("inclusion_reasons", "exclusion_reasons", "uncertainties")
METADATA_FIELDS = (
    "title", "publication_year", "publication_title", "doi", "html_url", "pdf_url",
)
CSV_FIELDS = (
    "candidate_id", "decision", "confidence", "inclusion_reasons",
    "exclusion_reasons", "uncertainties", "abstract_available",
    "download_priority", *METADATA_FIELDS,
)

ARTIFACT_VERSION = 1


# ---------------------------------------------------------------------------
# Screening packet
# ---------------------------------------------------------------------------


def _load_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        rows = data.get("items", data) if isinstance(data, dict) else data
        if not isinstance(rows, list):
            raise ValueError("candidate JSON must be an array or contain an items array")
        return [row for row in rows if isinstance(row, dict)]
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_screening_packet(candidates_path: Path, out_dir: Path) -> int:
    """Create an abstract-only screening packet from candidate records."""
    rows = [
        {k: v for k, v in row.items() if k not in FORBIDDEN_FIELDS}
        for row in _load_rows(candidates_path)
    ]
    out_dir.mkdir(parents=True, exist_ok=True)

    jsonl_path = out_dir / "screening_packet.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    fields = sorted({key for row in rows for key in row})
    with (out_dir / "screening_packet.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
                for k, v in row.items()
            })

    print(f"wrote {len(rows)} candidates to {jsonl_path}")
    return 0


# ---------------------------------------------------------------------------
# Agent screening import
# ---------------------------------------------------------------------------


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number} must contain a JSON object")
        rows.append(value)
    return rows


def _index_candidates(rows: list[dict[str, Any]]) -> tuple[list[str], dict[str, dict[str, Any]]]:
    order: list[str] = []
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = str(row.get("candidate_id") or "").strip()
        if not cid:
            raise ValueError("candidate_id is required in candidate input")
        if cid in indexed:
            raise ValueError(f"duplicate candidate id in candidate input: {cid}")
        order.append(cid)
        indexed[cid] = row
    return order, indexed


def _validate_agent_row(row: dict[str, Any], abstract_available: bool) -> dict[str, Any]:
    cid = str(row.get("candidate_id") or "").strip()
    decision = str(row.get("decision") or "").strip().lower()
    if decision not in DECISIONS:
        raise ValueError(f"{cid}: decision must be include, maybe, or exclude")

    confidence = row.get("confidence")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1:
        raise ValueError(f"{cid}: confidence must be a number from 0 to 1")

    priority = str(row.get("download_priority") or "").strip().lower()
    if priority not in PRIORITIES:
        raise ValueError(f"{cid}: download_priority must be none, low, medium, or high")

    normalized: dict[str, Any] = {
        "artifact_version": ARTIFACT_VERSION,
        "candidate_id": cid,
        "decision": decision,
        "confidence": confidence,
        "abstract_available": abstract_available,
        "download_priority": priority,
    }
    for field in LIST_FIELDS:
        values = row.get(field)
        if not isinstance(values, list) or any(
            not isinstance(v, str) or not v.strip() for v in values
        ):
            raise ValueError(f"{cid}: {field} must be an array of non-empty strings")
        normalized[field] = [v.strip() for v in values]

    if not abstract_available:
        if decision == "include":
            raise ValueError(f"{cid}: missing abstract cannot be included")
        if not normalized["uncertainties"]:
            raise ValueError(f"{cid}: missing abstract requires at least one uncertainty")
    return normalized


def import_agent_screening(
    candidates_path: Path, batch_paths: list[Path], out_dir: Path
) -> int:
    """Validate and merge agent-authored abstract-screening batches."""
    if not batch_paths:
        raise ValueError("at least one batch is required")

    order, candidates = _index_candidates(_read_jsonl(candidates_path))

    decisions: dict[str, dict[str, Any]] = {}
    for batch_path in batch_paths:
        for row in _read_jsonl(batch_path):
            cid = str(row.get("candidate_id") or "").strip()
            if not cid:
                raise ValueError(f"{batch_path}: candidate_id is required")
            if cid in decisions:
                raise ValueError(f"duplicate candidate id: {cid}")
            decisions[cid] = row

    unknown = sorted(set(decisions) - set(candidates))
    if unknown:
        raise ValueError(f"unknown candidate ids: {', '.join(unknown)}")
    missing = sorted(set(candidates) - set(decisions))
    if missing:
        raise ValueError(f"missing screening decisions: {', '.join(missing)}")

    merged: list[dict[str, Any]] = []
    for cid in order:
        candidate = candidates[cid]
        abstract_available = bool(str(candidate.get("abstract") or "").strip())
        item = _validate_agent_row(decisions[cid], abstract_available)
        for field in METADATA_FIELDS:
            value = candidate.get(field)
            item[field] = value if field == "publication_year" and isinstance(value, int) else str(value or "")
        merged.append(item)

    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "screening_stage1.jsonl").open("w", encoding="utf-8") as handle:
        for row in merged:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")

    with (out_dir / "screening_stage1.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for item in merged:
            row = {field: item.get(field, "") for field in CSV_FIELDS}
            for field in LIST_FIELDS:
                row[field] = json.dumps(row[field], ensure_ascii=True)
            row["abstract_available"] = str(row["abstract_available"]).lower()
            writer.writerow(row)

    counts = {d: sum(r["decision"] == d for r in merged) for d in DECISIONS}
    print(
        f"screened={len(merged)}; include={counts['include']}; "
        f"maybe={counts['maybe']}; exclude={counts['exclude']}"
    )
    return 0
