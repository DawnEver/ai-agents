#!/usr/bin/env python3
"""Parse the flat frontmatter block at the top of a reply draft.

The block is deliberately *flat* `key: value` lines, split on the first colon only, so
that `subject: Re: something` works without a YAML dependency. Value lists are
comma-separated and split quote-aware, so `"Smith, Bob" <bob@x>` survives intact.

Usage:
    from mail_frontmatter import parse, split_addresses, split_paths

    doc = parse(Path("final.md").read_text(encoding="utf-8"))
    doc.fields["to"], doc.body, doc.warnings
"""

from __future__ import annotations

from dataclasses import dataclass, field

FENCE = "---"
BOM = "﻿"

# Address-ish keys are parsed as mailboxes; `attach` as paths; the rest are opaque text.
ADDRESS_KEYS = frozenset({"to", "cc", "bcc", "from", "reply-to"})
PATH_KEYS = frozenset({"attach"})

EVENT_KEYS = frozenset(
    {
        "event.title",
        "event.start",
        "event.end",
        "event.timezone",
        "event.utc",
        "event.location",
        "event.description",
        "event.attendees",
        "event.organizer",
        "event.method",
        "event.uid",
    }
)

KNOWN_KEYS = frozenset({"subject", "date"}) | ADDRESS_KEYS | PATH_KEYS | EVENT_KEYS


def _split_items(value: str) -> list[str]:
    """Split on commas that are not inside a double-quoted display name or filename.

    `"Smith, Bob" <bob@example.com>` is one item, not two; so is `"report, final.pdf"`.
    """
    items: list[str] = []
    current: list[str] = []
    in_quotes = False
    for ch in value:
        if ch == '"':
            in_quotes = not in_quotes
            current.append(ch)
        elif ch == "," and not in_quotes:
            items.append("".join(current))
            current = []
        else:
            current.append(ch)
    items.append("".join(current))
    return [item.strip() for item in items if item.strip()]


@dataclass
class ParsedDoc:
    fields: dict[str, str] = field(default_factory=dict)
    body: str = ""
    warnings: list[str] = field(default_factory=list)

    def get(self, key: str, default: str = "") -> str:
        return self.fields.get(key, default) or default

    def addresses(self, key: str) -> list[str]:
        return split_addresses(self.get(key))

    def paths(self, key: str) -> list[str]:
        return split_paths(self.get(key))

    def event(self) -> dict[str, str]:
        return {k[len("event.") :]: v for k, v in self.fields.items() if k.startswith("event.")}


def split_addresses(value: str) -> list[str]:
    """Split an address list, tolerating quoted display names containing commas."""
    return _split_items(value)


def split_paths(value: str) -> list[str]:
    """Split an attachment path list, stripping surrounding quotes from each item."""
    out = []
    for item in _split_items(value):
        if len(item) >= 2 and item[0] == item[-1] and item[0] in "\"'":
            item = item[1:-1].strip()
        if item:
            out.append(item)
    return out


def parse(source: str) -> ParsedDoc:
    """Parse `source` into frontmatter fields plus the body that follows.

    A missing or unclosed frontmatter block is not an error here - the caller decides
    whether a block is required. Unrecognised keys are reported, because a typo silently
    dropping an attachment is the worst failure mode this format has.
    """
    doc = ParsedDoc()
    text = source.lstrip(BOM)
    lines = text.split("\n")

    start = 0
    while start < len(lines) and not lines[start].strip():
        start += 1

    if start >= len(lines) or lines[start].strip() != FENCE:
        doc.body = text
        return doc

    end = None
    for i in range(start + 1, len(lines)):
        if lines[i].strip() == FENCE:
            end = i
            break

    if end is None:
        doc.warnings.append(
            f"frontmatter opens with '{FENCE}' on line {start + 1} but is never closed - "
            f"treating the whole file as body"
        )
        doc.body = text
        return doc

    for offset, raw in enumerate(lines[start + 1 : end], start=start + 2):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            doc.warnings.append(f"line {offset}: not a 'key: value' pair, ignored: {line!r}")
            continue
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip()
        if key not in KNOWN_KEYS:
            doc.warnings.append(f"line {offset}: unknown frontmatter key {key!r} - ignored")
            continue
        if not value:
            # An empty value means "absent". Never emit a blank header from it.
            continue
        if key in doc.fields:
            doc.warnings.append(f"line {offset}: duplicate key {key!r} - last value wins")
        doc.fields[key] = value

    doc.body = "\n".join(lines[end + 1 :]).lstrip("\n")
    return doc
