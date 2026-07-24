"""Unified CLI entry point for Literature Review.

Macro commands for the 4-phase pipeline + post-acquisition capabilities.
Agent calls high-level commands; CLI handles mechanical steps internally.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from literature_review import __version__
from literature_review.acquire.download import (
    COMPLETION_MODES,
    DEFAULT_BROWSER_CHANNEL,
    DEFAULT_NETWORK_MODE,
    SUPPORTED_BROWSER_CHANNELS,
    SUPPORTED_NETWORK_MODES,
    open_login,
)
from literature_review.review.screen import import_agent_screening
from literature_review.pipeline.search import get_provider, run_dedupe_rank, run_probe
from literature_review.utils.paths import find_root

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
SEARCH_CONFIG = {"default_page_size": 25, "max_pages_per_query": 5}
DEFAULT_PAGE_SIZE = 25


RECOMMENDED_WORKFLOW = """Recommended workflow:

  lit-review init <topic>         Create workspace
  lit-review search --topic <s>   Queries -> probe -> search -> dedupe -> screening packet
  lit-review acquire --topic <s>  Queue -> auth -> download -> match -> manifest
  lit-review ingest --topic <s>   On-demand PDF decomposition with cache reuse

Post-acquisition (choose what you need):
  lit-review read --topic <s> --paper <id>   Deep-read with optional domain lens
  lit-review synthesize --topic <s>          Cross-paper synthesis
  lit-review export --topic <s>              Export cards to markdown/CSV/BibTeX
  lit-review stats --topic <s> [--plots]     Summary statistics + charts
  lit-review login                           Browser login for publisher auth
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _topic_dir(slug: str) -> Path:
    """Resolve a topic slug to its workspace directory."""
    d = find_root() / "workspaces" / slug
    if not d.exists():
        print(f"error: workspace not found: {d}", file=sys.stderr)
        print("Run: lit-review init <topic>", file=sys.stderr)
        raise SystemExit(2)
    return d


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lit-review",
        description="Literature Review - systematic literature review pipeline.",
        epilog=RECOMMENDED_WORKFLOW,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"Literature Review {__version__}")
    sub = parser.add_subparsers(dest="command")

    # === Pipeline: init ===
    p = sub.add_parser("init", help="Create a new workspace for a topic.")
    p.add_argument("topic", help="Topic name or slug.")

    # === Pipeline: search ===
    p = sub.add_parser("search", help="End-to-end: queries -> probe -> search -> dedupe -> screening packet.")
    p.add_argument("--topic", required=True, help="Topic slug (workspaces/<slug>).")
    p.add_argument("--provider", action="append", help="Literature source provider (repeatable; default: all from workspace.toml).")
    p.add_argument("--max-pages", type=int, default=5)
    p.add_argument("--rows-per-page", type=int, default=DEFAULT_PAGE_SIZE)
    p.add_argument("--delay", type=float, default=1.0, help="Seconds between pages.")
    p.add_argument("--probe-only", action="store_true", help="Stop after probe for query adjustment.")
    p.add_argument("--skip-probe", action="store_true", help="Skip probe, go straight to full search.")

    # === Pipeline: acquire ===
    p = sub.add_parser("acquire", help="End-to-end: queue -> auth -> download -> match -> manifest.")
    p.add_argument("--topic", required=True, help="Topic slug.")
    p.add_argument("--profile", help="Browser profile path for authenticated download.")
    p.add_argument("--candidate-id", action="append", help="Approve specific candidate (repeatable).")
    p.add_argument("--approved-by", default="user")
    p.add_argument("--queue-only", action="store_true", help="Only build the download queue.")

    # === Pipeline: ingest ===
    p = sub.add_parser("ingest", help="On-demand PDF decomposition with cache reuse.")
    p.add_argument("--topic", required=True, help="Topic slug.")
    p.add_argument("--paper", action="append", dest="paper_ids", help="Specific candidate ID (repeatable).")
    p.add_argument("--dry-run", action="store_true", help="Show what would be decomposed without doing it.")

    # === Agent support: import-screening ===
    p = sub.add_parser("import-screening", help="Validate and merge agent-authored screening batches.")
    p.add_argument("--topic", required=True, help="Topic slug.")
    p.add_argument("--batch", action="append", required=True, help="Path to batch result JSONL (repeatable).")

    # === Post-acquisition: read ===
    p = sub.add_parser("read", help="Deep-read a paper with optional domain lens.")
    p.add_argument("--topic", required=True, help="Topic slug.")
    p.add_argument("--paper", required=True, help="Candidate ID to read.")
    p.add_argument("--lens", help="Domain lens name (e.g. power_electronics).")
    p.add_argument("--model", help="Model override for AI reading.")

    # === Post-acquisition: synthesize ===
    p = sub.add_parser("synthesize", help="Cross-paper synthesis from reading cards.")
    p.add_argument("--topic", required=True, help="Topic slug.")
    p.add_argument("--paper", action="append", dest="paper_ids", help="Specific candidate IDs (repeatable).")
    p.add_argument("--model", help="Model override.")

    # === Post-acquisition: export ===
    p = sub.add_parser("export", help="Export paper cards to various formats.")
    p.add_argument("--topic", required=True, help="Topic slug.")
    p.add_argument("--format", default="markdown", choices=["markdown", "csv", "bibtex", "json"])
    p.add_argument("--paper", action="append", dest="paper_ids", help="Specific candidate IDs (repeatable).")

    # === Post-acquisition: stats ===
    p = sub.add_parser("stats", help="Summary statistics for the review.")
    p.add_argument("--topic", required=True, help="Topic slug.")
    p.add_argument("--plots", action="store_true", help="Generate matplotlib plots.")

    # === Utility: login ===
    p = sub.add_parser("login", help="Open a publisher site in a browser for authentication.")
    p.add_argument("--profile", default="ieee", help="Browser profile name.")
    p.add_argument("--url", default="https://ieeexplore.ieee.org/")
    p.add_argument("--browser-channel", choices=sorted(SUPPORTED_BROWSER_CHANNELS), default=DEFAULT_BROWSER_CHANNEL)
    p.add_argument("--completion", choices=sorted(COMPLETION_MODES), default="browser-close")
    p.add_argument("--network-mode", choices=sorted(SUPPORTED_NETWORK_MODES), default=DEFAULT_NETWORK_MODE)

    # === Micro-commands (kept for debugging / advanced use) ===
    p = sub.add_parser("probe", help="[Advanced] Probe queries against a provider.")
    p.add_argument("--queries", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--provider", default="ieee")
    p.add_argument("--query-id")

    p = sub.add_parser("dedupe-rank", help="[Advanced] Deduplicate and rank candidate JSONL files.")
    p.add_argument("--input", required=True, action="append")
    p.add_argument("--out", required=True)

    return parser


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

def _handle_init(args: argparse.Namespace) -> int:
    """Create workspace directory and workspace.toml."""
    import re
    from datetime import datetime, timezone

    slug = re.sub(r"[^a-z0-9]+", "-", args.topic.lower()).strip("-")
    ws_dir = find_root() / "workspaces" / slug

    if ws_dir.exists():
        print(f"Workspace already exists: {ws_dir}")
        return 0

    ws_dir.mkdir(parents=True, exist_ok=True)
    for sub in ("search", "screening", "download", "handoff", "ingest", "reading", "notes", "export"):
        (ws_dir / sub).mkdir(exist_ok=True)

    toml_content = (
        f'workspace_id = "{slug}"\n'
        f'name = "{args.topic}"\n'
        f'description = ""\n'
        f'created_at = "{datetime.now(timezone.utc).isoformat()}"\n'
        f'\n'
        f'lenses = []\n'
        f'providers = ["ieee_xplore"]\n'
        f'pdf_store = ""\n'
        f'parent = ""\n'
        f'\n'
        f'[zotero]\n'
        f'collection_key = ""\n'
        f'group_id = ""\n'
        f'sync_notes = true\n'
        f'sync_attachments = false\n'
        f'tags = []\n'
        f'\n'
        f'[defaults]\n'
        f'year_from = 2018\n'
        f'year_to = 2026\n'
        f'content_types = ["Journals", "Conferences"]\n'
        f'preferred_venues = []\n'
    )
    (ws_dir / "workspace.toml").write_text(toml_content, encoding="utf-8")
    print(f"Created workspace: {ws_dir}")
    return 0


def _handle_search(args: argparse.Namespace) -> int:
    td = _topic_dir(args.topic)
    try:
        from literature_review.pipeline.orchestrator import run_search as do_search
        result = do_search(
            td,
            provider=args.provider if args.provider else None,
            max_pages=args.max_pages,
            rows_per_page=args.rows_per_page,
            delay_seconds=args.delay,
            probe_only=args.probe_only,
            skip_probe=args.skip_probe,
        )
        print(f"search: candidates={result.get('candidates_count', 0)}")
        failures = result.get("failures") or []
        for f in failures:
            print(f"warning: {f['provider']} {f['stage']} failed: {f['error']}", file=sys.stderr)
        if failures and not result.get("candidates_count"):
            return 1
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _handle_acquire(args: argparse.Namespace) -> int:
    td = _topic_dir(args.topic)
    try:
        from literature_review.pipeline.orchestrator import run_acquire as do_acquire
        result = do_acquire(
            td,
            profile=args.profile,
            queue_only=args.queue_only,
            candidate_ids=args.candidate_id,
            approved_by=args.approved_by,
        )
        print(f"acquire: downloaded={result.get('downloaded', 0)}, manifest={result.get('manifest_path', 'none')}")
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _handle_ingest(args: argparse.Namespace) -> int:
    td = _topic_dir(args.topic)
    try:
        from literature_review.pipeline.orchestrator import run_ingest as do_ingest
        result = do_ingest(
            td,
            paper_ids=args.paper_ids,
            dry_run=args.dry_run,
        )
        if args.dry_run:
            print(f"ingest (dry-run): pending={result.get('pending', 0)}, cached={result.get('skipped', 0)}")
        else:
            print(f"ingest: ok={result.get('succeeded', 0)}, fail={result.get('failed', 0)}, skip={result.get('skipped', 0)}")
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _handle_import_screening(args: argparse.Namespace) -> int:
    td = _topic_dir(args.topic)
    candidates_path = td / "search" / "candidates_ranked.jsonl"
    out_path = td / "screening" / "screening_stage1.jsonl"
    if not candidates_path.exists():
        print(f"error: {candidates_path} not found. Run search first.", file=sys.stderr)
        return 2
    try:
        return import_agent_screening(candidates_path, [Path(p) for p in args.batch], out_path)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _handle_read(args: argparse.Namespace) -> int:
    td = _topic_dir(args.topic)
    try:
        from literature_review.pipeline.orchestrator import run_read as do_read
        card = do_read(td, args.paper, lens=args.lens, model=args.model)
        print(f"read: verdict={card.get('verdict', '?')}, confidence={card.get('confidence', 0):.0%}")
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _handle_synthesize(args: argparse.Namespace) -> int:
    td = _topic_dir(args.topic)
    try:
        from literature_review.pipeline.orchestrator import run_synthesize as do_synth
        synthesis = do_synth(td, paper_ids=args.paper_ids, model=args.model)
        print(synthesis[:500] + ("..." if len(synthesis) > 500 else ""))
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _handle_export(args: argparse.Namespace) -> int:
    td = _topic_dir(args.topic)
    try:
        from literature_review.pipeline.orchestrator import run_export as do_export
        out = do_export(td, format=args.format, paper_ids=args.paper_ids)
        print(f"exported: {out}")
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _handle_stats(args: argparse.Namespace) -> int:
    td = _topic_dir(args.topic)
    try:
        from literature_review.pipeline.orchestrator import run_stats as do_stats
        stats = do_stats(td, plots=args.plots)
        import json
        print(json.dumps(stats, indent=2, ensure_ascii=True, default=str))
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _handle_login(args: argparse.Namespace) -> int:
    profile = Path(args.profile)
    if not profile.is_absolute():
        import os
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        profile = Path(base) / "literature-review" / "browser-profiles" / args.profile
    return open_login(
        profile, args.url,
        browser_channel=args.browser_channel,
        completion=args.completion,
        network_mode=args.network_mode,
    )


def _handle_probe(args: argparse.Namespace) -> int:
    try:
        provider = get_provider(args.provider)
        return run_probe(
            queries_path=Path(args.queries), out_dir=Path(args.out),
            provider=provider, query_id=args.query_id,
            allow_unapproved_plan=True,
        )
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _handle_dedupe_rank(args: argparse.Namespace) -> int:
    return run_dedupe_rank([Path(p) for p in args.input], Path(args.out))


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

_HANDLERS: dict[str, object] = {
    "init": _handle_init,
    "search": _handle_search,
    "acquire": _handle_acquire,
    "ingest": _handle_ingest,
    "import-screening": _handle_import_screening,
    "read": _handle_read,
    "synthesize": _handle_synthesize,
    "export": _handle_export,
    "stats": _handle_stats,
    "login": _handle_login,
    "probe": _handle_probe,
    "dedupe-rank": _handle_dedupe_rank,
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
