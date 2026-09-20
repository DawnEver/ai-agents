#!/usr/bin/env python3
"""Turn a reply draft body into an HTML part and a plain-text part.

Deliberately a *minimal* markdown subset - the drafts this reads are LLM-written email
bodies, not documents. Supported: blank-line-separated paragraphs, `- ` bullet lists,
`**bold**`, `*italic*`, `[text](url)`, and `![alt](path)` for inline images.

Two rules matter more than the markup coverage:

* **Raw HTML in the body is escaped, never passed through.** The body is untrusted input.
* **Link targets are checked against a scheme allowlist.** Escaping alone does not stop
  `[x](javascript:...)`, because that payload rides in an attribute, not in text.

Usage:
    from mail_render import parse_blocks, render_html, render_plain, collect_image_paths

    blocks = parse_blocks(doc.body)
    paths = collect_image_paths(blocks)
    html, warnings = render_html(blocks, {"image-1.png": "<img-1@local>"})
    text = render_plain(blocks)
"""

from __future__ import annotations

import re
from dataclasses import dataclass

ALLOWED_SCHEMES = frozenset({"http", "https", "mailto", "cid", "tel"})

_SCHEME = re.compile(r"^([A-Za-z][A-Za-z0-9+.\-]*):")

# Image before link (the `!` prefix), bold before italic (the `**` prefix).
_INLINE = re.compile(
    r"!\[(?P<img_alt>[^\]]*)\]\((?P<img_path>[^)\s]+)\)"
    r"|\[(?P<link_text>[^\]]*)\]\((?P<link_url>[^)\s]+)\)"
    r"|\*\*(?P<bold>[^*]+)\*\*"
    r"|\*(?P<italic>[^*]+)\*"
)


@dataclass
class Text:
    value: str


@dataclass
class Bold:
    value: str


@dataclass
class Italic:
    value: str


@dataclass
class Link:
    text: str
    url: str
    safe: bool


@dataclass
class Image:
    alt: str
    path: str


@dataclass
class Paragraph:
    lines: list[list[object]]


@dataclass
class Bullets:
    items: list[list[object]]


def escape_text(value: str) -> str:
    """Escape for an HTML text node. Quotes are harmless here, so they are left alone."""
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def escape_attr(value: str) -> str:
    """Escape for a double-quoted HTML attribute value."""
    return escape_text(value).replace('"', "&quot;")


def url_is_safe(url: str) -> bool:
    """True when the URL has no scheme, or a scheme on the allowlist.

    Whitespace is stripped from inside the URL first so that `java\\nscript:` cannot slip
    past the scheme test.
    """
    cleaned = re.sub(r"[\s\x00-\x1f]", "", url)
    match = _SCHEME.match(cleaned)
    if not match:
        return True  # relative URL - nothing to hijack
    return match.group(1).lower() in ALLOWED_SCHEMES


def parse_inline(text: str) -> list[object]:
    """Tokenise one line's inline markup. Unmatched text comes back as `Text` tokens."""
    tokens: list[object] = []
    position = 0
    for match in _INLINE.finditer(text):
        if match.start() > position:
            tokens.append(Text(text[position : match.start()]))
        if match.group("img_path") is not None:
            tokens.append(Image(alt=match.group("img_alt"), path=match.group("img_path")))
        elif match.group("link_url") is not None:
            url = match.group("link_url")
            tokens.append(Link(text=match.group("link_text"), url=url, safe=url_is_safe(url)))
        elif match.group("bold") is not None:
            tokens.append(Bold(match.group("bold")))
        else:
            tokens.append(Italic(match.group("italic")))
        position = match.end()
    if position < len(text):
        tokens.append(Text(text[position:]))
    return tokens


def parse_blocks(body: str) -> list[object]:
    """Split a body into `Paragraph` and `Bullets` blocks."""
    blocks: list[object] = []
    paragraph: list[list[object]] = []
    bullets: list[list[object]] = []

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append(Paragraph(lines=list(paragraph)))
            paragraph.clear()

    def flush_bullets() -> None:
        if bullets:
            blocks.append(Bullets(items=list(bullets)))
            bullets.clear()

    for raw in body.split("\n"):
        line = raw.rstrip()
        if not line.strip():
            flush_paragraph()
            flush_bullets()
            continue
        stripped = line.lstrip()
        if stripped.startswith("- ") or stripped == "-":
            flush_paragraph()
            bullets.append(parse_inline(stripped[2:] if len(stripped) > 2 else ""))
            continue
        flush_bullets()
        paragraph.append(parse_inline(stripped))

    flush_paragraph()
    flush_bullets()
    return blocks


def collect_image_paths(blocks: list[object]) -> list[str]:
    """Every image path referenced in the body, in order, de-duplicated."""
    seen: dict[str, None] = {}
    for tokens in _iter_token_lists(blocks):
        for token in tokens:
            if isinstance(token, Image):
                seen.setdefault(token.path, None)
    return list(seen)


def _iter_token_lists(blocks: list[object]):
    for block in blocks:
        if isinstance(block, Paragraph):
            yield from block.lines
        elif isinstance(block, Bullets):
            yield from block.items


def _bare_cid(value: str) -> str:
    """Strip the angle brackets that a `Content-ID:` header carries but a `cid:` URL must not.

    `cid_for` values may be written either way; emitting `cid:<x@y>` would break the link.
    """
    value = value.strip()
    if value.startswith("<") and value.endswith(">"):
        return value[1:-1]
    return value


def _render_tokens_html(tokens: list[object], cid_for: dict[str, str], warnings: list[str]) -> str:
    out: list[str] = []
    for token in tokens:
        if isinstance(token, Text):
            out.append(escape_text(token.value))
        elif isinstance(token, Bold):
            out.append(f"<strong>{escape_text(token.value)}</strong>")
        elif isinstance(token, Italic):
            out.append(f"<em>{escape_text(token.value)}</em>")
        elif isinstance(token, Link):
            if token.safe:
                out.append(
                    f'<a href="{escape_attr(token.url)}">{escape_text(token.text)}</a>'
                )
            else:
                warnings.append(
                    f"link target {token.url!r} has a disallowed scheme - rendered as plain text"
                )
                out.append(escape_text(token.text))
        elif isinstance(token, Image):
            cid = cid_for.get(token.path)
            if cid:
                out.append(
                    f'<img src="cid:{escape_attr(_bare_cid(cid))}" '
                    f'alt="{escape_attr(token.alt)}">'
                )
            else:
                warnings.append(f"image {token.path!r} was not resolved - alt text shown instead")
                out.append(escape_text(token.alt))
    return "".join(out)


def render_html(blocks: list[object], cid_for: dict[str, str]) -> tuple[str, list[str]]:
    """Render blocks to an HTML document body, resolving images through `cid_for`."""
    warnings: list[str] = []
    parts: list[str] = []
    for block in blocks:
        if isinstance(block, Paragraph):
            rendered = [
                _render_tokens_html(line, cid_for, warnings) for line in block.lines
            ]
            parts.append("<p>" + "<br>\n".join(rendered) + "</p>")
        elif isinstance(block, Bullets):
            items = "".join(
                "<li>" + _render_tokens_html(item, cid_for, warnings) + "</li>\n"
                for item in block.items
            )
            parts.append("<ul>\n" + items + "</ul>")
    body = "\n".join(parts)
    return f"<html>\n<body>\n{body}\n</body>\n</html>", warnings


def _render_tokens_plain(tokens: list[object]) -> str:
    out: list[str] = []
    for token in tokens:
        if isinstance(token, (Text, Bold, Italic)):
            out.append(token.value)
        elif isinstance(token, Link):
            out.append(f"{token.text} <{token.url}>" if token.safe else token.text)
        elif isinstance(token, Image):
            out.append(f"[image: {token.alt}]")
    return "".join(out)


def render_plain(blocks: list[object]) -> str:
    """Render blocks to plain text, preserving what the HTML cannot carry.

    Images become an explicit `[image: alt]` marker rather than vanishing, and links keep
    their URL in angle brackets - a plain-text reader should not lose information that the
    HTML version conveys.
    """
    parts: list[str] = []
    for block in blocks:
        if isinstance(block, Paragraph):
            parts.append("\n".join(_render_tokens_plain(line) for line in block.lines))
        elif isinstance(block, Bullets):
            parts.append("\n".join("- " + _render_tokens_plain(item) for item in block.items))
    return "\n\n".join(parts)
