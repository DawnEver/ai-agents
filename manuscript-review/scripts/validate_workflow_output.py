"""Deterministically validate host-adapted manuscript workflow artifacts."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

class ContractError(ValueError):
    """A workflow artifact violates its on-disk contract."""

LITERATURE_HEADINGS = ("Paper Positioning", "Key References (from paper)",
                       "Related Work (IEEE search)", "Author Background",
                       "Research Landscape Summary")

def _read_nonempty(path: Path) -> str:
    if not path.is_file(): raise ContractError(f"missing file: {path}")
    text = path.read_text(encoding="utf-8").strip()
    if not text: raise ContractError(f"empty file: {path}")
    return text

def validate_literature(path: Path) -> None:
    headings = re.findall(r"^##\s+(.+?)\s*$", _read_nonempty(path), re.MULTILINE)
    missing = [h for h in LITERATURE_HEADINGS if h not in headings]
    if missing: raise ContractError(f"{path}: missing level-2 sections: {', '.join(missing)}")

def validate_critique(path: Path) -> None:
    text = _read_nonempty(path)
    points = list(re.finditer(r"^##\s+\d+\s*[·.:-]\s*.+$", text, re.MULTILINE))
    if not points: raise ContractError(f"{path}: no numbered critique points")
    starts = [p.start() for p in points] + [len(text)]
    for index, point in enumerate(points):
        block = text[point.start():starts[index + 1]]
        for field in ("Evidence", "Severity", "Suggested action"):
            if not re.search(rf"^-\s*{re.escape(field)}\s*:\s*\S", block, re.MULTILINE | re.IGNORECASE):
                raise ContractError(f"{path}: point {index + 1} missing {field}")
        severity = re.search(r"^-\s*Severity\s*:\s*(\S+)", block, re.MULTILINE | re.IGNORECASE)
        if severity and severity.group(1).lower() not in {"major", "minor", "nit"}:
            raise ContractError(f"{path}: point {index + 1} has invalid Severity")

def validate_fanout(directory: Path, angles: list[str], approval: Path | None = None) -> None:
    if not angles: raise ContractError("at least one expected angle is required")
    expected = set(angles)
    if len(expected) != len(angles):
        raise ContractError("expected angles must be unique")
    for angle in angles:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", angle):
            raise ContractError(f"unsafe angle name: {angle!r}")
        validate_critique(directory / f"{angle}.md")
    actual = {path.stem for path in directory.glob("*.md")} if directory.is_dir() else set()
    if actual != expected:
        extras = sorted(actual - expected)
        missing = sorted(expected - actual)
        details = []
        if missing: details.append(f"missing: {', '.join(missing)}")
        if extras: details.append(f"unexpected/stale: {', '.join(extras)}")
        raise ContractError(f"{directory}: critique set mismatch ({'; '.join(details)})")
    if approval is not None:
        try:
            record = json.loads(_read_nonempty(approval))
        except json.JSONDecodeError as error:
            raise ContractError(f"{approval}: invalid JSON: {error.msg}") from error
        if record.get("user_approved") is not True or record.get("approved_angles") != angles:
            raise ContractError(f"{approval}: does not approve the exact expected angle list")
        skipped = record.get("skipped_angles")
        valid_skipped = (isinstance(skipped, list) and bool(skipped)
                         and all(isinstance(a, str) and re.fullmatch(r"[A-Za-z0-9_-]+", a) for a in skipped)
                         and len(set(skipped)) == len(skipped))
        if not valid_skipped or expected.intersection(skipped):
            raise ContractError(f"{approval}: skipped_angles must be a non-empty disjoint list")

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="contract", required=True)
    literature = commands.add_parser("literature"); literature.add_argument("path", type=Path)
    fanout = commands.add_parser("fanout"); fanout.add_argument("directory", type=Path); fanout.add_argument("--approval", type=Path); fanout.add_argument("angles", nargs="+")
    args = parser.parse_args()
    try:
        validate_literature(args.path) if args.contract == "literature" else validate_fanout(args.directory, args.angles, args.approval)
    except ContractError as error:
        parser.exit(1, f"contract error: {error}\n")
    return 0

if __name__ == "__main__": raise SystemExit(main())
