#!/usr/bin/env python3
"""Read a saved `.eml` (RFC 822) message with the stdlib `email` package.

The counterpart to `mail_msg.py`: between them, every way the user has handed over an
incoming mail is covered, and `mail_read.read()` picks by content rather than by suffix.

Usage:
    from mail_eml import extract
    mail = extract(Path("incoming.eml"))
"""

from __future__ import annotations

import email
import email.policy
import email.utils
from pathlib import Path

from mail_read import Address, Attachment, MailReadError, ParsedMail, parse_addresses

# Outlook writes text parts as Windows-1252 often enough that assuming UTF-8 loses bodies.
FALLBACK_CHARSETS = ("utf-8", "cp1252", "latin-1")


def _decode(part: email.message.Message) -> str:
    payload = part.get_payload(decode=True)
    if payload is None:
        raw = part.get_payload()
        return raw if isinstance(raw, str) else ""
    charsets = []
    declared = part.get_content_charset()
    if declared:
        charsets.append(declared)
    charsets.extend(FALLBACK_CHARSETS)
    for charset in charsets:
        try:
            return payload.decode(charset)
        except (UnicodeDecodeError, LookupError):
            continue
    return payload.decode("utf-8", "replace")


def _addresses(message: email.message.Message, header: str) -> list[Address]:
    return parse_addresses([str(value) for value in message.get_all(header, [])])


def _header_date(message: email.message.Message):
    raw = message.get("Date")
    if not raw:
        return None
    try:
        parsed = email.utils.parsedate_to_datetime(str(raw))
    except (TypeError, ValueError):
        return None
    return parsed


def _is_attachment(part: email.message.Message) -> bool:
    if part.get_content_maintype() == "multipart":
        return False
    disposition = (part.get_content_disposition() or "").lower()
    if disposition == "attachment":
        return True
    filename = part.get_filename()
    return bool(filename) and disposition != "inline"


def extract(path: Path) -> ParsedMail:
    """Read an `.eml` file into a `ParsedMail`."""
    try:
        with path.open("rb") as handle:
            message = email.message_from_binary_file(handle, policy=email.policy.compat32)
    except OSError as exc:
        raise MailReadError(f"cannot read {path}: {exc}") from exc
    except Exception as exc:
        raise MailReadError(f"{path} is not a readable .eml file: {exc}") from exc

    warnings: list[str] = []
    plain_chunks: list[str] = []
    html_chunks: list[str] = []
    attachments: list[Attachment] = []

    for part in message.walk():
        if part.get_content_maintype() == "multipart":
            continue
        content_type = part.get_content_type()
        if _is_attachment(part):
            filename = part.get_filename()
            if not filename:
                filename = f"attachment.{content_type.split('/', 1)[-1]}"
                warnings.append(f"attachment with no filename, named {filename}")
            payload = part.get_payload(decode=True) or b""
            if not payload:
                warnings.append(f"attachment '{filename}' is empty")
                continue
            attachments.append(
                Attachment(filename=filename, content_type=content_type, data=payload)
            )
        elif content_type == "text/plain":
            plain_chunks.append(_decode(part))
        elif content_type == "text/html":
            html_chunks.append(_decode(part))
        elif content_type.startswith("image/"):
            # An image with no filename reads as an inline screenshot; keep it either way,
            # because a forwarded mail often carries its content only in the picture.
            payload = part.get_payload(decode=True) or b""
            if payload:
                content_id = str(part.get("Content-ID") or "").strip("<>")
                # A Content-ID is often already a filename (`image001.png`); only add the
                # subtype when it carries no extension of its own.
                name = part.get_filename() or content_id or "inline"
                if "." not in name.rsplit("/", 1)[-1]:
                    name = f"{name}.{content_type.split('/', 1)[-1]}"
                attachments.append(
                    Attachment(
                        filename=name,
                        content_type=content_type,
                        data=payload,
                        inline=(part.get_content_disposition() or "").lower() != "attachment",
                    )
                )

    body_plain = "\n".join(chunk for chunk in plain_chunks if chunk.strip())
    body_html = "\n".join(chunk for chunk in html_chunks if chunk.strip())
    # A forwarded mail is often signature-only, with everything meaningful living in a
    # screenshot or attachment - say so rather than returning a silently empty round.
    if not body_plain.strip() and not body_html.strip():
        warnings.append(
            "message body is empty - the content may live in a screenshot or attachment"
        )

    return ParsedMail(
        source=str(path),
        subject=str(message.get("Subject") or "").strip(),
        message_id=str(message.get("Message-ID") or "").strip(),
        sender=_first_address(message, "From"),
        to=_addresses(message, "To"),
        cc=_addresses(message, "Cc"),
        date=_header_date(message),
        body_plain=body_plain,
        body_html=body_html,
        attachments=attachments,
        warnings=warnings,
    )


def _first_address(message: email.message.Message, header: str) -> Address:
    found = _addresses(message, header)
    return found[0] if found else Address()
