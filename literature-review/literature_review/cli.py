"""Unified CLI entry point for Literature Review."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from literature_review import __version__
from literature_review.browser.download import (
    DEFAULT_LIMIT,
    AccessBlockedError,
    acquire_pdfs,
)
from literature_review.browser.login import (
    COMPLETION_MODES,
    DEFAULT_BROWSER_CHANNEL,
    DEFAULT_NETWORK_MODE,
    SUPPORTED_BROWSER_CHANNELS,
    SUPPORTED_NETWORK_MODES,
    open_login,
)
from literature_review.pipeline.acquire import (
    approve_download_queue,
    match_pdfs,
    write_download_manifest,
    write_download_queue,
)
from literature_review.pipeline.brief import confirm_brief, load_brief, validate_brief
from literature_review.pipeline.ingest import decompose_pdfs
from literature_review.pipeline.query import (
    DEFAULT_MAX_TOTAL,
    DEFAULT_MIN_TOTAL,
    confirm_queries,
    evaluate_queries,
)
from literature_review.pipeline.screen import (
    import_agent_screening,
    write_screening_packet,
)
from literature_review.pipeline.search import (
    get_provider,
    run_dedupe_rank,
    run_probe,
    run_search,
)
from literature_review.utils.schema import validate

# ---------------------------------------------------------------------------
# Inline defaults
# ---------------------------------------------------------------------------
SEARCH_CONFIG = {"default_page_size": 25, "max_pages_per_query": 5}
DEFAULT_PAGE_SIZE = 25


RECOMMENDED_WORKFLOW = """Recommended agent-orchestrated workflow:

1. Agent writes research_brief.yaml and presents concepts to the user.
2. validate-brief, then confirm-brief after the first explicit approval.
3. Agent writes queries.yaml and presents final Boolean expressions.
4. confirm-queries after the second explicit approval.
5. probe, evaluate-queries, search, and dedupe-rank.
6. make-screening-packet, then import-agent-screening.
7. make-download-queue and approve-download-queue for selected papers.
8. Stop. Run browser-login/acquire-pdf only after a separate download request.
9. After manifest creation, ask separately before running decompose-pdfs.
"""


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lit-review",
        description="Literature Review — agent-orchestrated systematic literature review pipeline.",
        epilog=RECOMMENDED_WORKFLOW,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version", action="version", version=f"Literature Review {__version__}"
    )
    sub = parser.add_subparsers(dest="command")

    # -- validate-brief --
    p = sub.add_parser("validate-brief", help="Validate a research brief before user review.")
    p.add_argument("--brief", required=True)

    # -- confirm-brief --
    p = sub.add_parser("confirm-brief", help="Record user approval of research scope and concepts.")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--approved-by", default="user")

    # -- confirm-queries --
    p = sub.add_parser("confirm-queries", help="Record user approval of final Boolean queries.")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--approved-by", default="user")

    # -- probe --
    p = sub.add_parser("probe", help="Probe page 1 for each enabled query via a provider.")
    p.add_argument("--queries", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--provider", default="ieee")
    p.add_argument("--query-id")
    p.add_argument("--allow-unapproved-plan", action="store_true")

    # -- evaluate-queries --
    p = sub.add_parser("evaluate-queries", help="Evaluate probe result counts and emit refinement suggestions.")
    p.add_argument("--queries", required=True)
    p.add_argument("--probe-results", required=True)
    p.add_argument("--samples")
    p.add_argument("--out", required=True)
    p.add_argument("--min-total", type=int, default=DEFAULT_MIN_TOTAL)
    p.add_argument("--max-total", type=int, default=DEFAULT_MAX_TOTAL)

    # -- search --
    p = sub.add_parser("search", help="Run bounded full metadata searches for eligible queries.")
    p.add_argument("--queries", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--provider", default="ieee")
    p.add_argument("--query-id")
    p.add_argument("--max-pages", type=int, default=int(SEARCH_CONFIG.get("max_pages_per_query", 5)))
    p.add_argument("--rows-per-page", type=int, default=DEFAULT_PAGE_SIZE)
    p.add_argument("--delay-seconds", type=float, default=1.0)
    p.add_argument("--evaluation", required=True, help="Path to query_refinement_suggestions.yaml.")
    p.add_argument("--allow-unapproved-plan", action="store_true")

    # -- normalize-candidates --
    p = sub.add_parser("normalize-candidates", help="Normalize raw provider records into candidate artifacts.")
    p.add_argument("--raw", required=True)
    p.add_argument("--query-id", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--provider", default="ieee")
    p.add_argument("--page", type=int, default=1)

    # -- dedupe-rank --
    p = sub.add_parser("dedupe-rank", help="Deduplicate and rank candidate JSONL files.")
    p.add_argument("--input", required=True, action="append", help="JSONL input; repeat for multiple files.")
    p.add_argument("--out", required=True)

    # -- make-screening-packet --
    p = sub.add_parser("make-screening-packet", help="Create an abstract-only screening packet.")
    p.add_argument("--candidates", required=True)
    p.add_argument("--out", required=True)

    # -- import-agent-screening --
    p = sub.add_parser("import-agent-screening", help="Validate and merge agent-authored screening batches.")
    p.add_argument("--candidates", required=True)
    p.add_argument("--batch", action="append", required=True)
    p.add_argument("--out", required=True)

    # -- make-download-queue --
    p = sub.add_parser("make-download-queue", help="Generate an unapproved PDF download queue.")
    p.add_argument("--screening", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--confirmed-by-user", action="store_true")

    # -- approve-download-queue --
    p = sub.add_parser("approve-download-queue", help="Approve selected queue entries.")
    p.add_argument("--queue", required=True)
    p.add_argument("--candidate-id", action="append", required=True)
    p.add_argument("--approved-by", required=True)

    # -- browser-login --
    p = sub.add_parser("browser-login", help="Open a provider site in a dedicated browser profile for login.")
    p.add_argument("--profile", required=True)
    p.add_argument("--url", default="https://ieeexplore.ieee.org/")
    p.add_argument(
        "--browser-channel", choices=sorted(SUPPORTED_BROWSER_CHANNELS), default=DEFAULT_BROWSER_CHANNEL
    )
    p.add_argument("--completion", choices=sorted(COMPLETION_MODES), default="browser-close")
    p.add_argument(
        "--network-mode", choices=sorted(SUPPORTED_NETWORK_MODES), default=DEFAULT_NETWORK_MODE
    )

    # -- acquire-pdf --
    p = sub.add_parser("acquire-pdf", help="Download approved PDFs using an authenticated browser profile.")
    p.add_argument("--queue", required=True)
    p.add_argument("--run-dir", required=True)
    p.add_argument("--profile", required=True)
    p.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    p.add_argument(
        "--browser-channel", choices=sorted(SUPPORTED_BROWSER_CHANNELS), default=DEFAULT_BROWSER_CHANNEL
    )
    p.add_argument(
        "--network-mode", choices=sorted(SUPPORTED_NETWORK_MODES), default=DEFAULT_NETWORK_MODE
    )

    # -- match-pdfs --
    p = sub.add_parser("match-pdfs", help="Match downloaded or manually dropped PDFs to the approved queue.")
    p.add_argument("--queue", required=True)
    p.add_argument("--run-dir", required=True)

    # -- make-download-manifest --
    p = sub.add_parser("make-download-manifest", help="Validate matched PDFs and stop at the handoff gate.")
    p.add_argument("--matches", required=True)
    p.add_argument("--out", required=True)

    # -- decompose-pdfs --
    p = sub.add_parser("decompose-pdfs", help="Decompose a validated PDF manifest after user confirmation.")
    p.add_argument("--manifest", required=True)
    p.add_argument("--run-dir", required=True)
    p.add_argument("--confirmed-by-user", action="store_true")

    # -- validate-schema --
    p = sub.add_parser("validate-schema", help="Validate an artifact against its JSON schema.")
    p.add_argument("--file", dest="file_path", help="Path to the artifact file.")
    p.add_argument("--schema", help="Path to a JSON schema file (auto-detected when omitted).")
    p.add_argument("artifact", nargs="?", help="Shorthand for --file.")

    return parser


# ---------------------------------------------------------------------------
# Handlers — one per subcommand, each returns an exit code
# ---------------------------------------------------------------------------


def _handle_validate_brief(args: argparse.Namespace) -> int:
    brief_path = Path(args.brief)
    try:
        brief = load_brief(brief_path)
        errors = validate_brief(brief)
        if errors:
            for error in errors:
                print(f"error: {error}", file=sys.stderr)
            return 2
        print(f"valid: {brief_path}")
        return 0
    except (OSError, ValueError, yaml.YAMLError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


def _handle_confirm_brief(args: argparse.Namespace) -> int:
    try:
        confirm_brief(Path(args.run_dir) / "research_brief.yaml", args.approved_by)
        print(f"confirmed: {Path(args.run_dir) / 'research_brief.yaml'}")
        return 0
    except (OSError, ValueError, yaml.YAMLError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


def _handle_confirm_queries(args: argparse.Namespace) -> int:
    try:
        return confirm_queries(Path(args.run_dir), args.approved_by)
    except (OSError, ValueError, yaml.YAMLError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


def _handle_probe(args: argparse.Namespace) -> int:
    try:
        provider = get_provider(args.provider)
        return run_probe(
            queries_path=Path(args.queries),
            out_dir=Path(args.out),
            provider=provider,
            query_id=args.query_id,
            allow_unapproved_plan=args.allow_unapproved_plan,
        )
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


def _handle_evaluate_queries(args: argparse.Namespace) -> int:
    return evaluate_queries(
        queries_path=Path(args.queries),
        probe_results_path=Path(args.probe_results),
        out_dir=Path(args.out),
        min_total=args.min_total,
        max_total=args.max_total,
        samples_path=Path(args.samples) if args.samples else None,
    )


def _handle_search(args: argparse.Namespace) -> int:
    try:
        provider = get_provider(args.provider)
        return run_search(
            queries_path=Path(args.queries),
            out_dir=Path(args.out),
            provider=provider,
            max_pages=args.max_pages,
            rows_per_page=args.rows_per_page,
            delay_seconds=args.delay_seconds,
            query_id=args.query_id,
            allow_unapproved_plan=args.allow_unapproved_plan,
            evaluation_path=Path(args.evaluation) if args.evaluation else None,
        )
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


def _handle_normalize_candidates(args: argparse.Namespace) -> int:
    """Normalize raw provider-specific records into the common candidate format."""
    import json as _json

    provider = get_provider(args.provider)
    raw_path = Path(args.raw)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Read raw JSON (expects {"records": [...]} or bare array)
        raw_data = _json.loads(raw_path.read_text(encoding="utf-8"))
        if isinstance(raw_data, dict):
            records = raw_data.get("records", [])
        elif isinstance(raw_data, list):
            records = raw_data
        else:
            raise ValueError(f"{raw_path} must contain a JSON object with 'records' or a JSON array")

        if not isinstance(records, list):
            raise ValueError(f"{raw_path} records field must be a list")

        out_path = out_dir / f"normalized_{args.query_id}.jsonl"
        count = 0
        with out_path.open("w", encoding="utf-8") as handle:
            for i, record in enumerate(records, start=1):
                if not isinstance(record, dict):
                    continue
                candidate = provider.normalize_record(
                    record, query_id=args.query_id,
                    rank=i, page=args.page, search_expression="",
                )
                handle.write(_json.dumps(candidate, ensure_ascii=True) + "\n")
                count += 1
        print(f"normalized {count} candidates from {raw_path}")
        return 0
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


def _handle_dedupe_rank(args: argparse.Namespace) -> int:
    return run_dedupe_rank([Path(p) for p in args.input], Path(args.out))


def _handle_make_screening_packet(args: argparse.Namespace) -> int:
    return write_screening_packet(Path(args.candidates), Path(args.out))


def _handle_import_agent_screening(args: argparse.Namespace) -> int:
    try:
        return import_agent_screening(
            Path(args.candidates),
            [Path(p) for p in args.batch],
            Path(args.out),
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


def _handle_make_download_queue(args: argparse.Namespace) -> int:
    try:
        return write_download_queue(
            screening_path=Path(args.screening),
            out_dir=Path(args.out),
            confirmed_by_user=args.confirmed_by_user,
        )
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


def _handle_approve_download_queue(args: argparse.Namespace) -> int:
    try:
        count = approve_download_queue(
            Path(args.queue), args.candidate_id, args.approved_by
        )
        print(f"approved={count}")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


def _handle_browser_login(args: argparse.Namespace) -> int:
    return open_login(
        Path(args.profile),
        args.url,
        browser_channel=args.browser_channel,
        completion=args.completion,
        network_mode=args.network_mode,
    )


def _handle_acquire_pdf(args: argparse.Namespace) -> int:
    try:
        rows = acquire_pdfs(
            Path(args.queue),
            Path(args.run_dir),
            limit=args.limit,
            profile=Path(args.profile),
            browser_channel=args.browser_channel,
            network_mode=args.network_mode,
        )
        print(f"downloaded={len(rows)}")
        return 0
    except (ValueError, AccessBlockedError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


def _handle_match_pdfs(args: argparse.Namespace) -> int:
    result = match_pdfs(Path(args.queue), Path(args.run_dir))
    print(
        f"matched={result['matched_count']}; "
        f"manual_review={len(result['manual_review'])}"
    )
    return 0


def _handle_make_download_manifest(args: argparse.Namespace) -> int:
    return write_download_manifest(Path(args.matches), Path(args.out))


def _handle_decompose_pdfs(args: argparse.Namespace) -> int:
    try:
        artifact = decompose_pdfs(
            Path(args.manifest), Path(args.run_dir), args.confirmed_by_user,
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    succeeded = sum(1 for item in artifact["ingests"] if item["status"] == "succeeded")
    failed = sum(1 for item in artifact["ingests"] if item["status"] == "failed")
    skipped = sum(1 for item in artifact["ingests"] if item["status"] == "skipped")
    return 2 if failed or skipped else 0


def _handle_validate_schema(args: argparse.Namespace) -> int:
    artifact_arg = args.file_path or args.artifact
    if not artifact_arg:
        return 0

    artifact_path = Path(artifact_arg)
    schema_path = Path(args.schema) if args.schema else None
    errors = validate(artifact_path, schema_path)
    if errors:
        for error in errors:
            print(f"error: {error}")
        return 1
    print(f"validated: {artifact_path}")
    return 0


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

_HANDLERS: dict[str, object] = {
    "validate-brief": _handle_validate_brief,
    "confirm-brief": _handle_confirm_brief,
    "confirm-queries": _handle_confirm_queries,
    "probe": _handle_probe,
    "evaluate-queries": _handle_evaluate_queries,
    "search": _handle_search,
    "normalize-candidates": _handle_normalize_candidates,
    "dedupe-rank": _handle_dedupe_rank,
    "make-screening-packet": _handle_make_screening_packet,
    "import-agent-screening": _handle_import_agent_screening,
    "make-download-queue": _handle_make_download_queue,
    "approve-download-queue": _handle_approve_download_queue,
    "browser-login": _handle_browser_login,
    "acquire-pdf": _handle_acquire_pdf,
    "match-pdfs": _handle_match_pdfs,
    "make-download-manifest": _handle_make_download_manifest,
    "decompose-pdfs": _handle_decompose_pdfs,
    "validate-schema": _handle_validate_schema,
}


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    handler = _HANDLERS.get(args.command)
    if handler is None:
        print(f"unknown command: {args.command}", file=sys.stderr)
        return 2
    return handler(args)  # type: ignore[operator]


if __name__ == "__main__":
    raise SystemExit(main())
