#!/usr/bin/env python3
"""Clear an archived round's leftover folder from `ongoing/`.

The archive procedure (AGENTS.md step 7) copies a round into `archived/` and removes the
source. The removal is refused by a global permission rule on `rm -rf`, so the source is
left behind — and the next round for the same slug then has to be written over it instead
of into a fresh directory.

This script performs the removal, but only after proving the archived copy already holds
every file the source has. Nothing is deleted on faith: an archive that is missing a file,
or holds a different version of one, is a refusal, not a warning.

Usage:
    python scripts/clear_ongoing.py ongoing/<topic> [--dry-run] [--json]

Exit codes:
    0  the round was removed, or --dry-run confirmed it could be
    1  the source is missing or not a round folder, or no archive covers it
"""

from __future__ import annotations

import argparse
import filecmp
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# `final.md` is renamed to `reply.md` at archive time (AGENTS.md step 7d); every other
# file keeps its name, so the comparison maps the one and matches the rest directly.
RENAMES = {"final.md": "reply.md"}

# What the archive procedure always leaves behind. A directory missing these is not an
# archived round, whatever else it happens to contain.
ARCHIVE_MARKERS = ("reply.md", "meta.md")


class ClearError(Exception):
    """The round cannot be cleared."""


def archive_candidates(archive_root: Path, slug: str) -> list[Path]:
    """Every archived round directory for `slug`, ordered oldest path first.

    Covers the canonical nested layouts `archived/YYYY/MM/DD/<slug>` and the `-r<N>`
    same-day repeats, plus the legacy flat `archived/YYYY-MM-DD/<slug>` from before the
    nested layout (AGENTS.md -> Thread reconstruction & globs).
    """
    patterns = ("*/*/*/" + slug, "*/*/*/" + slug + "-r*", "*/" + slug, "*/" + slug + "-r*")
    found = {path for pattern in patterns for path in archive_root.glob(pattern) if path.is_dir()}
    return sorted(found, key=lambda path: path.as_posix())


def verify(source: Path, archive: Path) -> list[str]:
    """Return every reason `archive` fails to cover `source`; empty means it covers it."""
    problems = [f"no {marker}" for marker in ARCHIVE_MARKERS if not (archive / marker).exists()]
    for item in sorted(source.iterdir()):
        if item.is_dir():
            problems.append(f"{item.name} is a directory, which a round never contains")
            continue
        target = archive / RENAMES.get(item.name, item.name)
        label = item.name if target.name == item.name else f"{item.name} (as {target.name})"
        if not target.exists():
            problems.append(f"{label} is missing")
        elif not filecmp.cmp(item, target, shallow=False):
            problems.append(f"{label} differs")
    return problems


def clear_round(source: Path, archive_root: Path, dry_run: bool = False) -> tuple[Path, list[str]]:
    """Remove `source`, once `archive_root` is proven to cover it.

    Returns the archive directory relied on and the names of the files removed. Raises
    `ClearError` when the source is not a round folder or no archive covers it.
    """
    if not source.is_dir():
        raise ClearError(f"{source} is not a directory")
    if source.parent.name != "ongoing":
        raise ClearError(f"{source} is not a round folder directly under ongoing/")

    candidates = archive_candidates(archive_root, source.name)
    if not candidates:
        raise ClearError(f"no archived round found for {source.name}")

    covering = [candidate for candidate in candidates if not verify(source, candidate)]
    if not covering:
        newest = candidates[-1]
        raise ClearError(
            f"no archived round covers {source.name}; "
            f"{newest} is the newest candidate and it " + ", ".join(verify(source, newest))
        )

    archive = covering[-1]
    removed = sorted(item.name for item in source.iterdir())
    if not dry_run:
        shutil.rmtree(source)
    return archive, removed


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="clear_ongoing.py",
        description="Remove a round from ongoing/ after verifying its archived copy covers it.",
    )
    parser.add_argument("round", metavar="ongoing/<topic>", type=Path, help="the round to clear")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="verify and report, but leave the round in place",
    )
    parser.add_argument("--json", action="store_true", help="machine-readable result on stdout")
    parser.add_argument(
        "--archive-root",
        type=Path,
        default=ROOT / "archived",
        help="archive tree to verify against (default: repo's archived/)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    try:
        archive, removed = clear_round(args.round, args.archive_root, dry_run=args.dry_run)
    except ClearError as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}))
        else:
            print(f"clear_ongoing: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(
            json.dumps(
                {
                    "ok": True,
                    "cleared": str(args.round),
                    "verified_against": str(archive),
                    "files": removed,
                    "dry_run": args.dry_run,
                }
            )
        )
    else:
        verb = "would clear" if args.dry_run else "cleared"
        print(f"{verb}: {args.round}")
        print(f"  verified against: {archive} ({len(removed)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
