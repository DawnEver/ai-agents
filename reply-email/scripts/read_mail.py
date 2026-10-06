#!/usr/bin/env python3
"""Read an incoming email file into a round's `original.txt`, with its attachments beside it.

The inbound counterpart to `build_mail.py`. Outlook saves a single message as `.msg` (an
OLE compound file, not RFC 822) and a forwarded or exported one as `.eml`; both are handled,
and the format is detected from the file's content rather than trusted from its extension.

Usage:
    python scripts/read_mail.py <mail.msg|mail.eml> [--out DIR] [--stdout] [--plain]
                               [--json] [--strict]

Exit codes:
    0  read successfully
    1  a read error, or warnings under --strict

Without `--out` nothing is written: the rendered `original.txt` goes to stdout, so the
message can be inspected before it lands in a round folder. With `--out DIR` (in this
project, `ongoing/<topic>/`) the text file and every attachment are written there.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mail_read  # noqa: E402


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="read_mail.py",
        description="Read a .msg or .eml file into a round's original.txt plus attachments.",
    )
    parser.add_argument("mail", type=Path, help="the incoming message (.msg or .eml)")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="round directory to write original.txt and attachments into",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="print original.txt even when --out writes it to disk",
    )
    parser.add_argument(
        "--plain",
        action="store_true",
        help="drop the [inline image: ...] markers from an HTML-only body",
    )
    parser.add_argument("--strict", action="store_true", help="treat warnings as failure")
    parser.add_argument("--json", action="store_true", help="machine-readable result on stdout")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    inline_images = not args.plain

    try:
        mail = mail_read.read(args.mail)
        text = mail_read.render_original_txt(mail, inline_images=inline_images)
    except mail_read.MailReadError as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}))
        else:
            print(f"read_mail: {exc}", file=sys.stderr)
        return 1

    written: list[str] = []
    if args.out is not None:
        try:
            written = [
                str(path)
                for path in mail_read.write_round(mail, args.out, inline_images=inline_images)
            ]
        except OSError as exc:
            if args.json:
                print(json.dumps({"ok": False, "error": str(exc)}))
            else:
                print(f"read_mail: cannot write into {args.out}: {exc}", file=sys.stderr)
            return 1

    if args.json:
        print(
            json.dumps(
                {
                    "ok": True,
                    "source": str(args.mail),
                    "subject": mail.subject,
                    "message_id": mail.message_id,
                    "from": str(mail.sender),
                    "to": [str(address) for address in mail.to],
                    "cc": [str(address) for address in mail.cc],
                    "date": mail_read.format_date(mail.date),
                    "written": written,
                    "attachments": [
                        {
                            "filename": attachment.filename,
                            "content_type": attachment.content_type,
                            "bytes": len(attachment.data),
                            "inline": attachment.inline,
                            "missing": attachment.missing,
                        }
                        for attachment in mail.attachments
                    ],
                    "warnings": mail.warnings,
                }
            )
        )
    else:
        if written:
            for path in written:
                print(f"written: {path}")
        if args.out is None or args.stdout:
            if written:
                print()
            print(text, end="" if text.endswith("\n") else "\n")
        for warning in mail.warnings:
            print(f"  warning: {warning}", file=sys.stderr)

    if args.strict and mail.warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
