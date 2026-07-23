"""Download queue, PDF matching, and pre-ingest manifest operations."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ARTIFACT_VERSION = 1
MIN_PDF_BYTES = 1024

INCLUDED_DECISIONS = {"include", "maybe"}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2, "none": 3, "": 3}
CSV_FIELDS = [
    "candidate_id", "title", "publication_year", "publication_title",
    "doi", "html_url", "pdf_url", "decision", "confidence",
    "inclusion_reasons", "exclusion_reasons", "uncertainties",
    "abstract_available", "download_priority", "approved",
]


# ---------------------------------------------------------------------------
# Shared PDF utilities
# ---------------------------------------------------------------------------


def safe_filename(value: str, max_length: int = 100) -> str:
    """Sanitise a string for use as a safe filename component."""
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value or "paper")
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ._") or "paper"
    return cleaned[:max_length].rstrip(" .")


def sha256_file(path: Path) -> str:
    """Return the hex-encoded SHA-256 digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_pdf(path: Path) -> None:
    """Raise if *path* is not a valid PDF file."""
    if not path.is_file():
        raise ValueError(f"not a valid PDF: file does not exist: {path}")
    with path.open("rb") as handle:
        signature = handle.read(5)
    if signature != b"%PDF-" or path.stat().st_size < MIN_PDF_BYTES:
        raise ValueError(f"not a valid PDF: {path}")


# ---------------------------------------------------------------------------
# Download queue
# ---------------------------------------------------------------------------


def _normalize_cell(value: Any) -> str:
    return str(value or "").strip()


def _read_screening(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        rows: list[dict[str, Any]] = []
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number} must contain a JSON object")
            rows.append(value)
        return rows
    # CSV
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"candidate_id", "decision"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path} missing required columns: {', '.join(sorted(missing))}")
        return [{k: _normalize_cell(v) for k, v in row.items()} for row in reader]


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = _normalize_cell(value)
    if not text:
        return []
    if text.startswith("["):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            pass
    return [item.strip() for item in text.split(";") if item.strip()]


def _queue_sort_key(row: dict[str, str]) -> tuple[int, int, str]:
    decision_rank = 0 if row.get("decision", "").lower() == "include" else 1
    priority_rank = PRIORITY_ORDER.get(row.get("download_priority", "").lower(), 3)
    return (priority_rank, decision_rank, row.get("candidate_id", ""))


def _build_queue_items(screening_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in screening_rows:
        cid = row.get("candidate_id", "")
        decision = row.get("decision", "").lower()
        priority = row.get("download_priority", "").lower()
        if not cid or cid in seen:
            continue
        if decision not in INCLUDED_DECISIONS or priority == "none":
            continue
        seen.add(cid)
        item: dict[str, Any] = {
            "candidate_id": cid,
            "title": row.get("title", ""),
            "publication_year": row.get("publication_year", ""),
            "publication_title": row.get("publication_title", ""),
            "doi": row.get("doi", ""),
            "html_url": row.get("html_url", ""),
            "pdf_url": row.get("pdf_url", ""),
            "decision": decision,
            "inclusion_reasons": _string_list(row.get("inclusion_reasons") or row.get("reasons")),
            "exclusion_reasons": _string_list(row.get("exclusion_reasons")),
            "uncertainties": _string_list(row.get("uncertainties")),
            "download_priority": priority or "none",
            "approved": False,
        }
        confidence = row.get("confidence")
        if confidence not in (None, ""):
            item["confidence"] = float(confidence)
        aa = row.get("abstract_available")
        if isinstance(aa, bool):
            item["abstract_available"] = aa
        elif _normalize_cell(aa).lower() in {"true", "false"}:
            item["abstract_available"] = _normalize_cell(aa).lower() == "true"
        items.append(item)
    return sorted(items, key=_queue_sort_key)


def _write_queue_csv(path: Path, items: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for item in items:
            row = {field: item.get(field, "") for field in CSV_FIELDS}
            for field in ("inclusion_reasons", "exclusion_reasons", "uncertainties"):
                row[field] = json.dumps(row[field], ensure_ascii=True)
            if isinstance(row["abstract_available"], bool):
                row["abstract_available"] = str(row["abstract_available"]).lower()
            row["approved"] = "false"
            writer.writerow(row)


def _screening_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_download_queue(
    screening_path: Path, out_dir: Path, confirmed_by_user: bool = False
) -> int:
    """Generate an unapproved download queue from screening output."""
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = _read_screening(screening_path)
    items = _build_queue_items(rows)
    _write_queue_csv(out_dir / "download_queue.csv", items)

    confirmation = {
        "confirmed": bool(confirmed_by_user),
        "confirmed_at": (
            datetime.now().astimezone().isoformat(timespec="seconds")
            if confirmed_by_user else None
        ),
        "confirmed_by": "user" if confirmed_by_user else None,
        "screening_sha256": _screening_digest(screening_path),
    }
    artifact = {
        "artifact_version": ARTIFACT_VERSION,
        "screening_confirmation": confirmation,
        "items": items,
    }
    (out_dir / "download_queue.json").write_text(
        json.dumps(artifact, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    print(f"queued={len(items)}; approved=false")
    return 0


def approve_download_queue(
    queue_path: Path, candidate_ids: list[str], approved_by: str
) -> int:
    """Approve selected queue entries and record the approver identity."""
    if not approved_by.strip():
        raise ValueError("approved_by is required")

    artifact = json.loads(queue_path.read_text(encoding="utf-8"))
    requested = set(candidate_ids)
    known = {str(item.get("candidate_id", "")) for item in artifact.get("items", [])}
    missing = requested - known
    if missing:
        raise ValueError(f"unknown candidate ids: {', '.join(sorted(missing))}")

    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    artifact.setdefault("screening_confirmation", {}).update({
        "confirmed": True, "confirmed_at": timestamp, "confirmed_by": approved_by.strip(),
    })

    count = 0
    for item in artifact.get("items", []):
        if item.get("candidate_id") in requested:
            item["approved"] = True
            item["approval"] = {"approved_by": approved_by.strip(), "approved_at": timestamp}
            count += 1

    queue_path.write_text(
        json.dumps(artifact, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )

    csv_path = queue_path.with_suffix(".csv")
    if csv_path.exists():
        _write_queue_csv(csv_path, artifact.get("items", []))
        approved_ids = {
            str(i.get("candidate_id"))
            for i in artifact.get("items", [])
            if i.get("approved") is True
        }
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        for row in rows:
            row["approved"] = "true" if row.get("candidate_id") in approved_ids else "false"
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(rows)

    return count


# ---------------------------------------------------------------------------
# PDF matching
# ---------------------------------------------------------------------------


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def _pdf_search_text(path: Path) -> str:
    raw = path.read_bytes()
    chunks = [raw[:250_000].decode("latin-1", errors="ignore")]
    try:
        from pypdf import PdfReader
        reader = PdfReader(path)
        chunks.extend((page.extract_text() or "") for page in reader.pages[:2])
    except Exception:
        pass
    return "\n".join(chunks).lower()


def _match_scores(path: Path, text: str, item: dict[str, Any]) -> int:
    haystack = _norm(path.stem + " " + text)
    scores = []
    doi = _norm(str(item.get("doi", "")))
    article = _norm(str(item.get("article_number") or item.get("articleNumber") or ""))
    candidate = _norm(str(item.get("candidate_id", "")))
    title = _norm(str(item.get("title", "")))
    if doi and doi in haystack:
        scores.append(100)
    if article and article in haystack:
        scores.append(90)
    if candidate and candidate in _norm(path.stem):
        scores.append(80)
    if len(title) >= 16 and title in haystack:
        scores.append(70)
    return max(scores, default=0)


def _maximum_weight_matching(
    scores: list[list[int]], forbidden: tuple[int, int] | None = None
) -> tuple[int, list[tuple[int, int]]]:
    """Return a maximum-total-score one-to-one matching, allowing unmatched PDFs."""
    states: dict[int, tuple[int, list[tuple[int, int]]]] = {0: (0, [])}
    for source_index, row in enumerate(scores):
        next_states = dict(states)
        for mask, (total, pairs) in states.items():
            for item_index, score in enumerate(row):
                if forbidden == (source_index, item_index):
                    continue
                bit = 1 << item_index
                if score <= 0 or mask & bit:
                    continue
                candidate = (total + score, pairs + [(source_index, item_index)])
                if candidate[0] > next_states.get(mask | bit, (-1, []))[0]:
                    next_states[mask | bit] = candidate
        states = next_states
    return max(states.values(), key=lambda v: v[0])


def match_pdfs(queue_path: Path, run_dir: Path) -> dict[str, Any]:
    """Match downloaded or manually dropped PDFs to approved queue records."""
    artifact = json.loads(queue_path.read_text(encoding="utf-8"))
    items = [item for item in artifact.get("items", []) if item.get("approved") is True]

    sources: list[Path] = []
    for directory in (run_dir / "pdfs", run_dir / "manual_drop"):
        if directory.exists():
            sources.extend(sorted(directory.glob("*.pdf")))

    matches, manual_review = [], []
    valid_sources: list[tuple[Path, str]] = []
    for path in sources:
        try:
            validate_pdf(path)
        except (ValueError, OSError) as error:
            manual_review.append({"pdf_path": str(path.resolve()), "reason": str(error)})
            continue
        valid_sources.append((path, _pdf_search_text(path)))

    score_matrix = [
        [_match_scores(path, text, item) for item in items]
        for path, text in valid_sources
    ]
    total_score, assignments = _maximum_weight_matching(score_matrix)

    # Reject ambiguous matchings
    if any(
        _maximum_weight_matching(score_matrix, pair)[0] == total_score
        for pair in assignments
    ):
        assignments = []

    assigned_sources = {si for si, _ in assignments}
    for si, (path, _) in enumerate(valid_sources):
        if si not in assigned_sources:
            manual_review.append({
                "pdf_path": str(path.resolve()), "reason": "no unique reliable match"
            })

    for source_index, index in assignments:
        path = valid_sources[source_index][0]
        item = items[index]
        destination = path
        if path.parent.name == "manual_drop":
            out = run_dir / "pdfs"
            out.mkdir(parents=True, exist_ok=True)
            cid = safe_filename(str(item.get("candidate_id") or "paper"), 40)
            ttl = safe_filename(str(item.get("title") or "paper"), 80)
            destination = out / f"{cid}_{ttl}.pdf"
            if destination.resolve() != path.resolve():
                shutil.copy2(path, destination)

        matches.append({
            "candidate_id": item.get("candidate_id", ""),
            "title": item.get("title", ""),
            "doi": item.get("doi", ""),
            "article_number": item.get("article_number") or item.get("articleNumber", ""),
            "pdf_path": str(destination.resolve()),
            "sha256": sha256_file(destination),
            "screening_reason": item.get("screening_reason") or item.get("reason", ""),
            "reading_questions": item.get("reading_questions", []),
        })

    result = {
        "matched_count": len(matches), "matches": matches,
        "manual_review": manual_review,
    }
    (run_dir / "pdf_match").mkdir(parents=True, exist_ok=True)
    (run_dir / "pdf_match" / "match_report.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    return result


# ---------------------------------------------------------------------------
# Download manifest
# ---------------------------------------------------------------------------


def _load_matches(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("matches") if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise ValueError("matches input must be an array or an object with a matches array")
    return rows


def _build_papers(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    papers: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        cid = str(row.get("candidate_id") or "").strip()
        title = str(row.get("title") or "").strip()
        raw_path = str(row.get("pdf_path") or "").strip()
        if not cid or not title or not raw_path:
            raise ValueError("each match requires candidate_id, title, and pdf_path")
        if cid in seen:
            raise ValueError(f"duplicate candidate_id: {cid}")
        seen.add(cid)

        pdf_path = Path(raw_path).expanduser().resolve()
        validate_pdf(pdf_path)

        questions = row.get("reading_questions") or []
        if not isinstance(questions, list) or not all(isinstance(q, str) for q in questions):
            raise ValueError(f"reading_questions must be a string array for {cid}")

        papers.append({
            "candidate_id": cid,
            "title": title,
            "doi": str(row.get("doi") or "").strip(),
            "article_number": str(row.get("article_number") or "").strip(),
            "pdf_path": str(pdf_path),
            "sha256": sha256_file(pdf_path),
            "screening_reason": str(row.get("screening_reason") or "").strip(),
            "reading_questions": questions,
        })
    return papers


def write_download_manifest(matches_path: Path, out_dir: Path) -> int:
    """Create a validated pre-ingest PDF download manifest."""
    papers = _build_papers(_load_matches(matches_path))
    artifact = {
        "artifact_version": ARTIFACT_VERSION,
        "manifest_type": "download_manifest",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "papers": papers,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "download_manifest.json"
    manifest_path.write_text(
        json.dumps(artifact, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )

    # Write human-readable summary
    lines = [
        "# Download Manifest", "",
        f"Validated PDFs: {len(papers)}",
        f"Machine-readable manifest: `{manifest_path.resolve()}`", "",
    ]
    for paper in papers:
        lines.extend([
            f"## {paper['candidate_id']}: {paper['title']}", "",
            f"- PDF: `{paper['pdf_path']}`",
            f"- SHA-256: `{paper['sha256']}`",
            f"- Screening reason: {paper['screening_reason'] or 'Not recorded'}",
        ])
        if paper["reading_questions"]:
            lines.append("- Reading questions: " + "; ".join(paper["reading_questions"]))
        lines.append("")
    lines.extend([
        "## Handoff Gate", "",
        "Do you want to decompose all validated PDFs with `paper_pdf_ingest` now?",
        "No decomposition or detailed-reading work has been started.", "",
    ])
    (out_dir / "download_manifest.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"validated={len(papers)}; handoff gate reached")
    print("Do you want to decompose all validated PDFs with paper_pdf_ingest now?")
    return 0
