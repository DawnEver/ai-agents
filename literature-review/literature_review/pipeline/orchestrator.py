"""Pipeline orchestrators — high-level functions that compose micro-steps.

Each orchestrator handles one phase end-to-end, so the agent calls one function
instead of orchestrating 10+ CLI commands. The CLI also wraps these for direct use.

Architecture:
  run_search(topic_dir)    → brief→queries→probe→search→normalize→dedupe→screening-packet
  run_acquire(topic_dir)   → screening→queue→download→match→manifest
  run_ingest(topic_dir)    → manifest→cache-check→decompose-selected
  run_read(topic_dir, ...) → deep-read paper(s) → PaperCard(s)
  run_synthesize(topic_dir) → cross-paper synthesis
  run_export(topic_dir)    → render cards + plots
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from literature_review.utils.state import mark_step


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _ensure(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    _ensure(path.parent)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=True) + "\n")
    return path


# ---------------------------------------------------------------------------
# 1. Search pipeline
# ---------------------------------------------------------------------------

def run_search(
    topic_dir: Path,
    *,
    provider: str = "ieee",
    max_pages: int = 5,
    rows_per_page: int = 25,
    delay_seconds: float = 1.0,
    probe_only: bool = False,
    skip_probe: bool = False,
) -> dict[str, Any]:
    """Run end-to-end search: brief → queries → probe → search → normalize → dedupe → screening packet.

    Args:
        topic_dir: Path to workspaces/<slug>/
        provider: Provider name (default 'ieee')
        max_pages: Maximum pages per query for full search
        probe_only: If True, stop after probe (for query adjustment)
        skip_probe: If True, skip probe and go straight to full search

    Returns:
        Dict with keys: queries_path, probe_results, candidates_count, screening_packet_path
    """
    from literature_review.providers.base import BaseProvider
    from literature_review.pipeline.search import get_provider, run_probe, run_search as _run_search, run_dedupe_rank
    from literature_review.review.screen import write_screening_packet
    from literature_review.utils.schema import load_data

    mark_step(topic_dir, "search", "in_progress")
    prov: BaseProvider = get_provider(provider)

    brief_path = topic_dir / "research_brief.toml"
    queries_path = topic_dir / "queries.toml"
    search_dir = _ensure(topic_dir / "search")

    if not brief_path.exists():
        raise FileNotFoundError(f"research_brief.toml not found in {topic_dir}. Run define step first.")

    result: dict[str, Any] = {
        "queries_path": str(queries_path),
        "probe_results": None,
        "candidates_count": 0,
        "screening_packet_path": None,
        "records_path": None,
    }

    # --- Probe ---
    if not skip_probe:
        print("=== Probe ===")
        probe_dir = _ensure(search_dir / "probe")
        _ = run_probe(
            queries_path=queries_path,
            out_dir=search_dir,
            provider=prov,
            allow_unapproved_plan=True,  # no SHA-256 gate in new architecture
        )
        result["probe_results"] = str(probe_dir / "probe_summary.csv")

        if probe_only:
            mark_step(topic_dir, "search", "probed",
                      queries_path=str(queries_path),
                      probe_results=result["probe_results"])
            return result

        # Evaluate probe results
        from literature_review.pipeline.query import evaluate_queries
        evaluate_queries(
            queries_path=queries_path,
            probe_results_path=probe_dir,
            out_dir=search_dir / "evaluation",
        )

    # --- Full search ---
    print("=== Full Search ===")
    queries_search_dir = _ensure(search_dir / "queries")
    _run_search(
        queries_path=queries_path,
        out_dir=search_dir,
        provider=prov,
        max_pages=max_pages,
        rows_per_page=rows_per_page,
        delay_seconds=delay_seconds,
        allow_unapproved_plan=True,
        evaluation_path=search_dir / "evaluation" / "query_refinement_suggestions.toml" if not skip_probe else None,
    )

    # --- Normalize candidates ---
    print("=== Normalize ===")
    plan = load_data(queries_path)
    query_list = plan.get("queries", []) if isinstance(plan, dict) else []
    all_candidates: list[dict[str, Any]] = []

    for query in query_list:
        if not isinstance(query, dict) or not query.get("enabled", True):
            continue
        qid = str(query.get("query_id", ""))
        raw_dir = search_dir / "search" / "raw"
        if raw_dir.exists():
            for raw_file in sorted(raw_dir.glob(f"{qid}_page_*.json")):
                raw_data = json.loads(raw_file.read_text(encoding="utf-8"))
                records = raw_data.get("records", []) if isinstance(raw_data, dict) else raw_data
                if not isinstance(records, list):
                    continue
                # Extract page number from filename
                import re
                page_match = re.search(r"page_(\d+)", raw_file.name)
                page = int(page_match.group(1)) if page_match else 1
                for i, record in enumerate(records, 1):
                    if isinstance(record, dict):
                        candidate = prov.normalize_record(
                            record, query_id=qid,
                            rank=(page - 1) * rows_per_page + i,
                            page=page, search_expression=str(query.get("expression", "")),
                        )
                        all_candidates.append(candidate)

        # Also check per-query normalized files
        norm_dir = queries_search_dir / qid
        if norm_dir.exists():
            for nf in norm_dir.glob("normalized_*.jsonl"):
                all_candidates.extend(_read_jsonl(nf))

    if all_candidates:
        _write_jsonl(search_dir / "queries" / "all_candidates.jsonl", all_candidates)

    # --- Deduplicate & rank ---
    print("=== Deduplicate & Rank ===")
    input_paths = []
    all_cand_path = search_dir / "queries" / "all_candidates.jsonl"
    if all_cand_path.exists():
        input_paths.append(all_cand_path)
    # Also collect from per-query directories
    for qdir in queries_search_dir.iterdir():
        if qdir.is_dir():
            for nf in qdir.glob("normalized_*.jsonl"):
                input_paths.append(nf)

    if input_paths:
        run_dedupe_rank(input_paths, search_dir)
    else:
        # Fallback: use records.jsonl from full search
        records_path = search_dir / "search" / "records.jsonl"
        if records_path.exists():
            run_dedupe_rank([records_path], search_dir)

    result["records_path"] = str(search_dir / "candidates_ranked.jsonl")
    result["candidates_count"] = len(_read_jsonl(search_dir / "candidates_ranked.jsonl"))

    # --- Make screening packet ---
    print("=== Screening Packet ===")
    screening_dir = _ensure(topic_dir / "screening")
    records_path = Path(result["records_path"])
    if records_path.exists():
        write_screening_packet(records_path, screening_dir)
        result["screening_packet_path"] = str(screening_dir / "screening_packet.jsonl")

    mark_step(topic_dir, "search", "done",
              candidates_count=result["candidates_count"],
              screening_packet_path=result["screening_packet_path"])

    return result


# ---------------------------------------------------------------------------
# 2. Acquire pipeline
# ---------------------------------------------------------------------------

def run_acquire(
    topic_dir: Path,
    *,
    profile: str | None = None,
    browser_channel: str = "chromium",
    queue_only: bool = False,
    candidate_ids: list[str] | None = None,
    approved_by: str = "user",
) -> dict[str, Any]:
    """Run end-to-end acquisition: screening → queue → download → match → manifest.

    Args:
        topic_dir: Path to workspaces/<slug>/
        profile: Browser profile path for authenticated download
        queue_only: If True, only build the queue (for user review)
        candidate_ids: Specific candidate IDs to approve (if None, prompt)
        approved_by: Identity for approval stamp

    Returns:
        Dict with keys: queue_path, downloaded, failed, manifest_path
    """
    from literature_review.pipeline.acquire import (
        approve_download_queue,
        match_pdfs,
        write_download_manifest,
        write_download_queue,
    )

    mark_step(topic_dir, "acquire", "in_progress")

    screening_path = topic_dir / "screening" / "screening_stage1.jsonl"
    download_dir = _ensure(topic_dir / "download")
    handoff_dir = _ensure(topic_dir / "handoff")

    if not screening_path.exists():
        raise FileNotFoundError(f"{screening_path} not found. Run search & screen step first.")

    result: dict[str, Any] = {
        "queue_path": str(download_dir / "download_queue.json"),
        "downloaded": 0,
        "failed": 0,
        "manifest_path": None,
    }

    # --- Build queue ---
    print("=== Build Download Queue ===")
    write_download_queue(screening_path, download_dir)

    if queue_only:
        mark_step(topic_dir, "acquire", "queued", queue_path=result["queue_path"])
        return result

    # --- Approve ---
    queue_path = download_dir / "download_queue.json"
    if candidate_ids:
        approve_download_queue(queue_path, candidate_ids, approved_by)
    else:
        # Auto-approve all 'include' decisions
        queue_data = json.loads(queue_path.read_text(encoding="utf-8"))
        include_ids = [
            str(item["candidate_id"])
            for item in queue_data.get("items", [])
            if item.get("decision") == "include"
        ]
        if include_ids:
            approve_download_queue(queue_path, include_ids, approved_by)

    # --- Download ---
    print("=== Download PDFs ===")
    try:
        from literature_review.acquire.download import acquire_pdfs
        rows = acquire_pdfs(
            queue_path, topic_dir,
            limit=100,
            profile=Path(profile) if profile else None,
            browser_channel=browser_channel,
        )
        result["downloaded"] = len(rows)
    except Exception as exc:
        print(f"Download error: {exc}")
        result["failed"] = 1
        mark_step(topic_dir, "acquire", "failed", error=str(exc))
        return result

    # --- Match ---
    print("=== Match PDFs ===")
    match_result = match_pdfs(queue_path, topic_dir)
    result["matched"] = match_result.get("matched_count", 0)

    # --- Manifest ---
    print("=== Create Manifest ===")
    match_report = topic_dir / "download" / "pdf_match" / "match_report.json"
    if match_report.exists():
        write_download_manifest(match_report, handoff_dir)
        result["manifest_path"] = str(handoff_dir / "download_manifest.json")

    mark_step(topic_dir, "acquire", "done",
              downloaded=result["downloaded"],
              matched=result["matched"],
              manifest_path=result["manifest_path"])

    return result


# ---------------------------------------------------------------------------
# 3. Ingest pipeline
# ---------------------------------------------------------------------------

def run_ingest(
    topic_dir: Path,
    *,
    paper_ids: list[str] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Run on-demand ingestion with cache check.

    Args:
        topic_dir: Path to workspaces/<slug>/
        paper_ids: Specific candidate IDs to decompose. None = all pending.
        dry_run: If True, only report what would be done.

    Returns:
        Dict with keys: succeeded, failed, skipped, pending
    """
    from literature_review.pipeline.ingest import decompose_pdfs

    mark_step(topic_dir, "ingest", "in_progress")

    manifest_path = topic_dir / "handoff" / "download_manifest.json"
    ingest_dir = _ensure(topic_dir / "ingest")

    if not manifest_path.exists():
        raise FileNotFoundError(f"{manifest_path} not found. Run acquire step first.")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    papers = manifest.get("papers", [])

    # Check cache
    succeeded, failed, skipped, pending = [], [], [], []
    for paper in papers:
        cid = str(paper["candidate_id"])
        output_dir = ingest_dir / cid
        if output_dir.exists() and (output_dir / "1-paper-text" / "paper.md").exists():
            skipped.append(cid)
        elif paper_ids is None or cid in paper_ids:
            pending.append(cid)
        else:
            skipped.append(cid)  # user didn't request this one

    result = {
        "succeeded": len(succeeded),
        "failed": len(failed),
        "skipped": len(skipped),
        "pending": len(pending),
        "pending_ids": pending,
        "skipped_ids": skipped,
    }

    if dry_run:
        mark_step(topic_dir, "ingest", "pending", **result)
        return result

    if not pending:
        print(f"All papers already decomposed ({len(skipped)} cached).")
        mark_step(topic_dir, "ingest", "done", **result)
        return result

    # Decompose only pending papers
    print(f"Decomposing {len(pending)} papers ({len(skipped)} cached, skipped)...")
    artifact = decompose_pdfs(manifest_path, topic_dir, confirmed_by_user=True)

    # Re-count after decomposition
    final_succeeded = sum(1 for i in artifact.get("ingests", []) if i["status"] == "succeeded")
    final_failed = sum(1 for i in artifact.get("ingests", []) if i["status"] == "failed")
    final_skipped = sum(1 for i in artifact.get("ingests", []) if i["status"] == "skipped")

    result.update({
        "succeeded": final_succeeded,
        "failed": final_failed,
        "skipped": final_skipped + len(skipped),
    })

    mark_step(topic_dir, "ingest", "done", **result)
    return result


# ---------------------------------------------------------------------------
# 4. Deep read (wires orphaned review_paper)
# ---------------------------------------------------------------------------

def run_read(
    topic_dir: Path,
    candidate_id: str,
    *,
    lens: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """Deep-read a single paper and produce a PaperCard.

    Args:
        topic_dir: Path to workspaces/<slug>/
        candidate_id: Which paper to read
        lens: Optional domain lens name (e.g. 'power_electronics')
        model: Optional model override

    Returns:
        PaperCard as dict
    """
    from literature_review.models import ResearchBrief
    from literature_review.review.reader import review_paper
    from literature_review.utils.schema import load_data

    # Load the decomposed paper text
    ingest_dir = topic_dir / "ingest" / candidate_id
    paper_md = ingest_dir / "1-paper-text" / "paper.md"
    if not paper_md.exists():
        raise FileNotFoundError(f"Paper not decomposed: {paper_md}. Run ingest step first.")

    paper_text = paper_md.read_text(encoding="utf-8")
    # Also collect per-section markdown
    md_dir = ingest_dir / "1-paper-text" / "md"
    if md_dir.exists():
        sections = sorted(md_dir.glob("*.md"))
        for sec in sections:
            paper_text += "\n\n" + sec.read_text(encoding="utf-8")

    # Load brief for criteria context
    brief_path = topic_dir / "research_brief.toml"
    brief_data = load_data(brief_path) if brief_path.exists() else {}
    brief = ResearchBrief(
        brief_id=str(brief_data.get("brief_id", "")),
        original_request=str(brief_data.get("original_request", "")),
        research_objective=str(brief_data.get("research_objective", "")),
        inclusion_criteria=brief_data.get("inclusion_criteria", []),
        exclusion_criteria=brief_data.get("exclusion_criteria", []),
        concepts=[],  # Simplified — core reading doesn't need full concept taxonomy
    )

    # Load lens if specified
    lens_data: dict[str, Any] | None = None
    if lens:
        lens_path = Path("lenses") / f"{lens}.toml"
        if lens_path.exists():
            lens_data = load_data(lens_path)

    # If lens provides context, prepend to paper text
    if lens_data:
        checklist = lens_data.get("technical_checklist", [])
        red_flags = lens_data.get("red_flags", [])
        if checklist or red_flags:
            lens_context = "\n\n## Domain Lens Context\n"
            if checklist:
                lens_context += "\n### Technical Checklist\n"
                for item in checklist:
                    lens_context += f"- [{item.get('category', '')}] {item.get('item', '')}\n"
            if red_flags:
                lens_context += "\n### Red Flags to Watch For\n"
                for rf in red_flags:
                    lens_context += f"- [{rf.get('severity', 'warning')}] {rf.get('flag', '')}: {rf.get('explanation', '')}\n"
            paper_text = lens_context + paper_text

    # Deep read
    card = review_paper(
        paper_text=paper_text,
        brief=brief,
        model_spec=model,
        candidate_id=candidate_id,
        title="",  # Will be extracted from paper.md
    )

    # Write output
    from dataclasses import asdict as _asdict
    reading_dir = _ensure(topic_dir / "reading")
    card_dict: dict[str, Any] = _asdict(card)  # type: ignore[arg-type]
    card_path = reading_dir / f"{candidate_id}_card.json"
    card_path.write_text(json.dumps(card_dict, indent=2, ensure_ascii=True, default=str), encoding="utf-8")

    # Render markdown
    from literature_review.export.render import paper_card_to_markdown
    md = paper_card_to_markdown(card)
    (reading_dir / f"{candidate_id}_card.md").write_text(md, encoding="utf-8")

    return card_dict


# ---------------------------------------------------------------------------
# 5. Cross-paper synthesis (wires orphaned compare_papers)
# ---------------------------------------------------------------------------

def run_synthesize(
    topic_dir: Path,
    *,
    paper_ids: list[str] | None = None,
    model: str | None = None,
) -> str:
    """Synthesize findings across deep-read papers.

    Args:
        topic_dir: Path to workspaces/<slug>/
        paper_ids: Specific paper candidate IDs. None = all with cards.
        model: Optional model override

    Returns:
        Synthesis text (markdown)
    """
    from literature_review.models import PaperCard
    from literature_review.review.synthesis import compare_papers

    reading_dir = topic_dir / "reading"
    if not reading_dir.exists():
        raise FileNotFoundError(f"No reading directory: {reading_dir}. Deep-read papers first.")

    cards: list[PaperCard] = []
    for card_path in sorted(reading_dir.glob("*_card.json")):
        cid = card_path.stem.replace("_card", "")
        if paper_ids and cid not in paper_ids:
            continue
        card_data = json.loads(card_path.read_text(encoding="utf-8"))
        cards.append(PaperCard(**{k: v for k, v in card_data.items()
                                   if k in PaperCard.__dataclass_fields__}))

    if not cards:
        raise ValueError("No paper cards found. Deep-read some papers first.")

    synthesis = compare_papers(cards, model_spec=model)

    # Write output
    notes_dir = _ensure(topic_dir / "notes")
    (notes_dir / "synthesis.md").write_text(synthesis, encoding="utf-8")

    return synthesis


# ---------------------------------------------------------------------------
# 6. Export & stats (wires orphaned render + plot)
# ---------------------------------------------------------------------------

def run_export(
    topic_dir: Path,
    *,
    format: str = "markdown",  # markdown | csv | bibtex | json
    paper_ids: list[str] | None = None,
) -> Path:
    """Export paper cards in the requested format.

    Args:
        topic_dir: Path to workspaces/<slug>/
        format: Output format
        paper_ids: Specific papers. None = all cards.

    Returns:
        Path to exported file
    """
    from literature_review.export.render import cards_to_csv
    from literature_review.models import PaperCard

    reading_dir = topic_dir / "reading"
    cards: list[PaperCard] = []
    for card_path in sorted(reading_dir.glob("*_card.json")):
        cid = card_path.stem.replace("_card", "")
        if paper_ids and cid not in paper_ids:
            continue
        card_data = json.loads(card_path.read_text(encoding="utf-8"))
        cards.append(PaperCard(**{k: v for k, v in card_data.items()
                                   if k in PaperCard.__dataclass_fields__}))

    export_dir = _ensure(topic_dir / "export")

    if format == "csv":
        out = export_dir / "papers.csv"
        cards_to_csv(cards, out)
    elif format == "json":
        out = export_dir / "papers.json"
        out.write_text(json.dumps([c.__dict__ for c in cards], indent=2, ensure_ascii=True, default=str), encoding="utf-8")
    elif format == "bibtex":
        out = export_dir / "references.bib"
        entries = []
        for card in cards:
            entries.append(f"@article{{{card.candidate_id},\n"
                          f"  title = {{{card.title}}},\n"
                          f"  note = {{{card.one_sentence}}},\n"
                          f"}}")
        out.write_text("\n\n".join(entries), encoding="utf-8")
    else:  # markdown
        from literature_review.export.render import paper_card_to_markdown
        out = export_dir / "papers.md"
        parts = [paper_card_to_markdown(c) for c in cards]
        out.write_text("\n\n---\n\n".join(parts), encoding="utf-8")

    return out


def run_stats(
    topic_dir: Path,
    *,
    plots: bool = False,
) -> dict[str, Any]:
    """Generate summary statistics for the review.

    Args:
        topic_dir: Path to workspaces/<slug>/
        plots: If True, generate matplotlib plots

    Returns:
        Stats dict
    """
    stats: dict[str, Any] = {}

    # Search stats
    ranked_path = topic_dir / "search" / "candidates_ranked.jsonl"
    if ranked_path.exists():
        candidates = _read_jsonl(ranked_path)
        stats["total_candidates"] = len(candidates)
        years_raw = [c.get("publication_year") for c in candidates]
        years = [int(y) for y in years_raw if y is not None]
        if years:
            stats["year_range"] = f"{min(years)}-{max(years)}"
        venues = set(c.get("venue", "") for c in candidates if c.get("venue"))
        stats["unique_venues"] = len(venues)

    # Screening stats
    screening_path = topic_dir / "screening" / "screening_stage1.jsonl"
    if screening_path.exists():
        screened = _read_jsonl(screening_path)
        decisions = {}
        for s in screened:
            d = s.get("decision", "unknown")
            decisions[d] = decisions.get(d, 0) + 1
        stats["screening"] = decisions

    # Download stats
    manifest_path = topic_dir / "handoff" / "download_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        stats["downloaded"] = len(manifest.get("papers", []))

    # Ingest stats
    ingest_manifest = topic_dir / "ingest" / "ingest_manifest.json"
    if ingest_manifest.exists():
        im = json.loads(ingest_manifest.read_text(encoding="utf-8"))
        stats["decomposed"] = sum(1 for i in im.get("ingests", []) if i["status"] == "succeeded")

    # Reading stats
    reading_dir = topic_dir / "reading"
    if reading_dir.exists():
        stats["deep_read"] = len(list(reading_dir.glob("*_card.json")))

    # Write stats
    stats_path = topic_dir / "notes" / "stats.json"
    _ensure(topic_dir / "notes")
    stats_path.write_text(json.dumps(stats, indent=2, ensure_ascii=True), encoding="utf-8")

    # Plots
    if plots and ranked_path.exists():
        try:
            from literature_review.export.plot import plot_year_distribution, plot_venue_distribution
            from literature_review.models import Candidate
            candidates = []
            for c in _read_jsonl(ranked_path):
                try:
                    candidates.append(Candidate(
                        candidate_id=str(c.get("candidate_id", "")),
                        source_provider=str(c.get("source_provider", "")),
                        title=str(c.get("title", "")),
                        abstract=str(c.get("abstract", "")),
                        venue=str(c.get("venue", "")),
                        publication_year=c.get("publication_year"),
                        doi=str(c.get("doi", "")),
                    ))
                except Exception:
                    pass
            plot_dir = _ensure(topic_dir / "export" / "plots")
            plot_year_distribution(candidates, plot_dir / "year_distribution.png")
            plot_venue_distribution(candidates, plot_dir / "venue_distribution.png")
            stats["plots"] = str(plot_dir)
        except Exception as exc:
            stats["plot_error"] = str(exc)

    return stats
