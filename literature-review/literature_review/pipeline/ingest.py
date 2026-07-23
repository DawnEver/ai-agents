"""PDF decomposition — drives paper_pdf_ingest against a confirmed manifest."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from literature_review.pipeline.acquire import sha256_file, validate_pdf
from literature_review.utils.schema import SCHEMAS_DIR, load_data, validate_json_schema

ARTIFACT_VERSION = 1


def _safe_component(value: str, fallback: str) -> str:
    component = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return component[:80] or fallback


def _validate_ingest_output(output_dir: Path) -> None:
    required = [
        output_dir / "0-raw.pdf",
        output_dir / "1-paper-text" / "paper.md",
        output_dir / "1-paper-text" / "INDEX.md",
    ]
    missing = [str(p) for p in required if not p.is_file()]
    section_dir = output_dir / "1-paper-text" / "md"
    if not section_dir.is_dir() or not any(section_dir.glob("*.md")):
        missing.append(str(section_dir / "*.md"))
    if missing:
        raise ValueError("ingest output is incomplete: " + ", ".join(missing))


def _write_manifest_atomic(path: Path, artifact: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(artifact, f, indent=2, ensure_ascii=True)
            f.write("\n")
    except BaseException:
        os.unlink(tmp)
        raise
    os.replace(tmp, path)


def _ingest_one(pdf_path: Path, out_dir: Path) -> None:
    """Run paper_pdf_ingest on a single PDF using its public Python API."""
    from paper_pdf_ingest import (
        clean_sections,
        convert,
        split_sections,
        write_paper_output,
    )
    from paper_pdf_ingest.convert import augment_markdown_with_formulas
    from paper_pdf_ingest.utils import slug

    raw_dest = out_dir / "0-raw.pdf"
    if pdf_path != raw_dest:
        shutil.copy2(pdf_path, raw_dest)

    text_dir = out_dir / "1-paper-text"
    (text_dir / "img" / "flat").mkdir(parents=True, exist_ok=True)

    md_text, _tool = convert(pdf_path, text_dir)
    md_text = augment_markdown_with_formulas(md_text, pdf_path)

    raw_sections = split_sections(md_text)
    main_sections, appended_papers = clean_sections(raw_sections)

    if not main_sections:
        raise RuntimeError("no sections found in PDF")

    write_paper_output(main_sections, text_dir, md_text, pdf_path=pdf_path)

    appended_dir = text_dir / "appended"
    if appended_dir.exists():
        shutil.rmtree(appended_dir, ignore_errors=True)
    if appended_papers:
        appended_dir.mkdir(parents=True, exist_ok=True)
        for i, (title, ap_sections) in enumerate(appended_papers, 1):
            ap_dir = appended_dir / f"{i:02d}-{slug(title) or f'paper-{i}'}"
            ap_dir.mkdir(parents=True, exist_ok=True)
            ap_img = ap_dir / "img" / "flat"
            ap_img.mkdir(parents=True, exist_ok=True)
            src_flat = text_dir / "img" / "flat"
            if src_flat.exists():
                for img in src_flat.iterdir():
                    if img.is_file():
                        shutil.copy2(img, ap_img / img.name)
            write_paper_output(ap_sections, ap_dir,
                               ap_sections[0][1] if ap_sections else "",
                               title_override=title, pdf_path=pdf_path)

    shutil.rmtree(text_dir / "_marker_tmp", ignore_errors=True)
    shutil.rmtree(text_dir / "img" / "flat", ignore_errors=True)


def decompose_pdfs(
    manifest_path: Path,
    run_dir: Path,
    confirmed_by_user: bool,
) -> dict[str, Any]:
    """Decompose every validated PDF only after explicit user confirmation."""
    if not confirmed_by_user:
        raise ValueError("PDF decomposition requires explicit user confirmation")

    manifest_path = manifest_path.expanduser().resolve()
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)

    schema = load_data(SCHEMAS_DIR / "download_manifest.schema.json")
    errors = validate_json_schema(manifest, schema)
    if errors:
        raise ValueError("invalid download manifest:\n" + "\n".join(errors))

    run_dir = run_dir.expanduser().resolve()
    ingest_root = run_dir / "ingest"
    ingest_root.mkdir(parents=True, exist_ok=True)

    ingests: list[dict[str, Any]] = []
    candidate_ids = [str(p["candidate_id"]) for p in manifest["papers"]]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("download manifest contains duplicate candidate_id values")

    used: set[str] = set()
    for paper in manifest["papers"]:
        cid = str(paper["candidate_id"])
        slug_name = _safe_component(cid, "paper")
        if slug_name in used:
            slug_name = f"{slug_name}-{hashlib.sha256(cid.encode()).hexdigest()[:8]}"
        used.add(slug_name)
        output_dir = ingest_root / slug_name

        record: dict[str, Any] = {
            "candidate_id": cid, "pdf_path": str(paper["pdf_path"]),
            "output_path": str(output_dir), "status": "failed",
        }

        if output_dir.exists():
            record.update(status="skipped", error="output directory already exists")
            ingests.append(record)
            continue

        temp_dir: Path | None = None
        try:
            pdf_path = Path(str(paper["pdf_path"])).expanduser().resolve()
            record["pdf_path"] = str(pdf_path)
            temp_dir = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}-", dir=ingest_root))
            staged = temp_dir / ".source.pdf"
            shutil.copy2(pdf_path, staged)
            validate_pdf(staged)
            if sha256_file(staged) != str(paper["sha256"]):
                raise ValueError(f"PDF SHA-256 changed: {pdf_path}")

            _ingest_one(staged, temp_dir)
            staged.unlink()
            _validate_ingest_output(temp_dir)
            temp_dir.rename(output_dir)
            temp_dir = None
            record["status"] = "succeeded"
        except Exception as exc:
            record["error"] = str(exc)[-2000:]
        finally:
            if temp_dir is not None:
                shutil.rmtree(temp_dir, ignore_errors=True)
        ingests.append(record)

    artifact = {
        "artifact_version": ARTIFACT_VERSION,
        "manifest_type": "ingest_manifest",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_manifest": str(manifest_path),
        "source_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "confirmed_by_user": True,
        "ingests": ingests,
    }
    ingest_schema = load_data(SCHEMAS_DIR / "ingest_manifest.schema.json")
    errors = validate_json_schema(artifact, ingest_schema)
    if errors:
        raise ValueError("invalid ingest manifest:\n" + "\n".join(errors))
    _write_manifest_atomic(ingest_root / "ingest_manifest.json", artifact)

    for item in ingests:
        print(f"{item['candidate_id']}: {item['status']}; output={item['output_path']}")
        if item.get("error"):
            print(f"  error: {item['error']}")
    succeeded = sum(1 for i in ingests if i["status"] == "succeeded")
    failed = sum(1 for i in ingests if i["status"] == "failed")
    skipped = sum(1 for i in ingests if i["status"] == "skipped")
    print(f"succeeded={succeeded}; failed={failed}; skipped={skipped}")
    return artifact
