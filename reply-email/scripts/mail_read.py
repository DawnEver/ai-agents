#!/usr/bin/env python3
"""Shared model for an incoming email, however it arrived.

`mail_msg.py` (Outlook `.msg`) and `mail_eml.py` (RFC 822 `.eml`) both produce a
`ParsedMail`; everything downstream - rendering `original.txt`, writing attachments into a
round folder - works on that one shape, so the two readers stay independent of each other.

The HTML-to-text pass exists because Outlook routinely sends HTML-only mail with no
`text/plain` alternative at all, and `original.txt` is the file a later continuation reads.

Usage:
    from mail_read import read, render_original_txt, write_round

    mail = read(Path("incoming.msg"))
    print(render_original_txt(mail))
"""

from __future__ import annotations

import email.utils
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

# Block-level tags end a line; everything else is inline. `<br>` is handled separately.
BLOCK_TAGS = frozenset(
    {
        "address", "article", "aside", "blockquote", "dd", "div", "dl", "dt", "fieldset",
        "figcaption", "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6",
        "header", "hr", "li", "main", "nav", "ol", "p", "pre", "section", "table", "tbody",
        "td", "tfoot", "th", "thead", "tr", "ul",
    }
)
# Elements whose text is markup machinery, not prose.
SKIP_TAGS = frozenset({"script", "style", "head", "title"})
# Outlook wraps the whole message in these; they are not content boundaries.
SKIP_CLASSES = frozenset({"x_msoelement"})
INLINE_IMAGE_NOTE = "[inline image: {}]"
# Structural markers, held out of the whitespace collapse below and resolved at the end.
PARA = "\x00"
BREAK = "\x01"


class MailReadError(RuntimeError):
    """The file could not be read as mail at all."""


@dataclass
class Address:
    """One mailbox. Either half may be missing; `email` is what a reply needs."""

    name: str = ""
    email: str = ""

    def __str__(self) -> str:
        if self.name and self.email:
            return f"{self.name} <{self.email}>"
        return self.name or self.email


def parse_addresses(values: list[str]) -> list[Address]:
    """Split raw header values into mailboxes, keeping display names intact.

    Shared by both readers: a `.msg` reaches this through its stored transport headers and
    an `.eml` through its own headers, and the two must agree on the result.
    """
    if not values:
        return []
    pairs = email.utils.getaddresses([str(value) for value in values])
    return [Address(name=name.strip(), email=addr.strip()) for name, addr in pairs if name or addr]


@dataclass
class Attachment:
    """A file carried by the message, inline images included."""

    filename: str
    content_type: str = "application/octet-stream"
    data: bytes = b""
    inline: bool = False
    # Partly-seen attachments (a by-reference entry whose bytes are not in the file).
    missing: bool = False

    def describe(self) -> str:
        size = f"{len(self.data):,} bytes"
        flags = ", inline" if self.inline else ""
        if self.missing:
            flags += ", body not present"
        return f"{self.filename} ({self.content_type}, {size}{flags})"


@dataclass
class ParsedMail:
    """A received message, normalized across `.msg` and `.eml`."""

    source: str = ""
    subject: str = ""
    # The incoming Message-ID is what a reply's In-Reply-To/References must quote, so it
    # is surfaced here and written into `original.txt` for the draft's frontmatter.
    message_id: str = ""
    sender: Address = field(default_factory=Address)
    to: list[Address] = field(default_factory=list)
    cc: list[Address] = field(default_factory=list)
    date: datetime | None = None
    body_plain: str = ""
    body_html: str = ""
    attachments: list[Attachment] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def recipients(self) -> list[Address]:
        return [*self.to, *self.cc]

    def body_text(self, *, inline_images: bool = True) -> str:
        """The readable body: `text/plain` if there was one, else the HTML converted.

        Returns the plain part verbatim when present - it is the sender's own rendering,
        and re-flowing it through the HTML pass would only lose fidelity.
        """
        if self.body_plain.strip():
            return self.body_plain.strip()
        return html_to_text(self.body_html, inline_images=inline_images)


class _HtmlToText(HTMLParser):
    """Collect visible text, turning block elements into paragraph breaks."""

    def __init__(self, *, inline_images: bool) -> None:
        super().__init__(convert_charrefs=True)
        self.inline_images = inline_images
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key.lower(): (value or "") for key, value in attrs}
        classes = set(attributes.get("class", "").split())
        if tag in SKIP_TAGS or (classes & SKIP_CLASSES):
            self._skip_depth += 1
            return
        if tag == "br":
            self.parts.append(BREAK)
        elif tag == "img" and self.inline_images:
            # The image bytes are written beside original.txt; this marker is what makes
            # the text file self-explanatory when read on its own.
            self.parts.append(BREAK + INLINE_IMAGE_NOTE.format(_image_name(attributes)) + BREAK)
        elif tag in BLOCK_TAGS:
            self.parts.append(PARA)

    def handle_endtag(self, tag: str) -> None:
        if tag in SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag in BLOCK_TAGS:
            self.parts.append(PARA)

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self.parts.append(data)

    def text(self) -> str:
        return "".join(self.parts)


def _image_name(attributes: dict[str, str]) -> str:
    """A readable label for an inline image, from `alt` or the `src` basename."""
    raw = (attributes.get("alt") or attributes.get("src") or "").strip()
    if raw.lower().startswith("cid:"):
        raw = raw[4:]
    # `src` is usually `cid:image001.jpg@01DD4AB1.C06F0130`; only the name is useful.
    return raw.rsplit("@", 1)[0].rsplit("/", 1)[-1] or "unnamed"


def html_to_text(html: str, *, inline_images: bool = True) -> str:
    """Convert an HTML mail body to readable plain text.

    Deliberately not a general-purpose converter: it keeps paragraph structure and drops
    everything else, because the output is a record of what the sender wrote.

    Source line breaks are *not* preserved - in HTML they are ordinary whitespace, and a
    mail client's hard wrapping would otherwise reappear as false sentence breaks. Only
    block elements produce paragraph breaks here.
    """
    if not html.strip():
        return ""
    parser = _HtmlToText(inline_images=inline_images)
    try:
        parser.feed(html)
        parser.close()
    except Exception:  # a malformed body should degrade, not lose the message
        pass

    text = parser.text()
    # Collapse every run of whitespace (including the &nbsp; that Outlook litters the body
    # with) to a single space, leaving the structural markers untouched.
    text = re.sub(r"[^\S\x00\x01]+", " ", text)
    text = text.replace(BREAK, "\n")
    text = re.sub(r" ?" + PARA + r" ?", "\n\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+(?=\n)", "", text)
    text = re.sub(r"^[ \t]+", "", text, flags=re.MULTILINE)
    return text.strip()


def format_date(value: datetime | None) -> str:
    if value is None:
        return ""
    if value.tzinfo is None:
        return value.strftime("%Y-%m-%d %H:%M")
    return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _address_line(label: str, addresses: list[Address]) -> str:
    return f"{label}: {', '.join(str(a) for a in addresses if str(a))}"


def render_original_txt(mail: ParsedMail, *, inline_images: bool = True) -> str:
    """Render the message as the round's `original.txt`.

    The header block is not decoration: the reply address, the subject and the date all
    get pulled from here when the draft's frontmatter is written.
    """
    lines: list[str] = []
    if mail.sender:
        lines.append(f"From: {mail.sender}")
    if mail.to:
        lines.append(_address_line("To", mail.to))
    if mail.cc:
        lines.append(_address_line("Cc", mail.cc))
    if mail.date:
        lines.append(f"Date: {format_date(mail.date)}")
    if mail.subject:
        lines.append(f"Subject: {mail.subject}")
    if mail.message_id:
        lines.append(f"Message-ID: {mail.message_id}")
    if mail.source:
        lines.append(f"Source: {mail.source}")

    lines.append("")
    lines.append(mail.body_text(inline_images=inline_images))

    if mail.attachments:
        lines.append("")
        lines.append("Attachments:")
        for attachment in mail.attachments:
            lines.append(f"  - {attachment.describe()}")

    if mail.warnings:
        lines.append("")
        lines.append("Read warnings:")
        for warning in mail.warnings:
            lines.append(f"  - {warning}")

    return "\n".join(lines).rstrip() + "\n"


def unique_name(filename: str, used: set[str]) -> str:
    """Return a filename that does not collide with one already written.

    Outlook reuses `image001.jpg`/`image.png` across every inline image in a message, so a
    naive write silently keeps only the last one. Suffix with a counter instead.
    """
    candidate = filename or "attachment"
    if candidate not in used:
        return candidate
    stem, dot, suffix = candidate.rpartition(".")
    if not dot:
        stem, suffix = candidate, ""
    index = 2
    while True:
        attempt = f"{stem}-{index}.{suffix}" if suffix else f"{stem}-{index}"
        if attempt not in used:
            return attempt
        index += 1


def safe_filename(filename: str) -> str:
    """Flatten a path-like attachment name to a bare filename.

    Attachment names arrive from the network and are written straight to disk, so anything
    that could traverse (`../`, absolute paths, drive letters) is stripped here.
    """
    cleaned = filename.replace("\\", "/").split("/")[-1].strip()
    cleaned = re.sub(r'[<>:"|?*\x00-\x1f]', "_", cleaned)
    cleaned = cleaned.strip(". ") or "attachment"
    return cleaned


def write_round(mail: ParsedMail, out_dir: Path, *, inline_images: bool = True) -> list[Path]:
    """Write `original.txt` plus every attachment into `out_dir`. Returns what was written."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    original = out_dir / "original.txt"
    original.write_text(render_original_txt(mail, inline_images=inline_images), encoding="utf-8")
    written.append(original)

    used: set[str] = {original.name}
    for attachment in mail.attachments:
        if attachment.missing:
            continue
        name = unique_name(safe_filename(attachment.filename), used)
        used.add(name)
        target = out_dir / name
        target.write_bytes(attachment.data)
        written.append(target)

    return written


def read(path: Path) -> ParsedMail:
    """Read a `.msg` or `.eml` by content, falling back to the suffix."""
    import mail_eml
    import mail_msg

    if not path.is_file():
        raise MailReadError(f"no such file: {path}")

    head = path.read_bytes()[:8]
    if head.startswith(mail_msg.CFB_SIGNATURE):
        return mail_msg.extract(path)
    if path.suffix.lower() == ".msg":
        # A .msg that is not an OLE container is corrupt, not an .eml in disguise.
        raise MailReadError(f"{path} has a .msg extension but is not an OLE compound file")
    return mail_eml.extract(path)
