#!/usr/bin/env python3
"""Build an importable `.eml` and/or `.ics` next to a finished reply draft.

The draft carries its addressing in a flat frontmatter block; the body below it is the
email itself. By default the `.eml` is left unmarked, so Outlook opens it as a **received
message** and Reply works; `--draft` adds `X-Unsent: 1` to open it as a compose window with
a Send button instead. The two are mutually exclusive - a message cannot be both already
sent and not yet sent. The `.ics` is a plain appointment unless the round asks for a real
meeting request.

Usage:
    python scripts/build_mail.py <final.md> [--out DIR] [--eml] [--ics] [--text-only]
                                           [--name STEM] [--eol lf] [--draft] [--strict]
                                           [--json]

Exit codes:
    0  built successfully
    1  a build error (nothing usable written), or warnings under --strict

Output names come from the round directory (the topic slug), not the markdown filename -
archiving renames `final.md` to `reply.md`, so a filename-derived output would drift.
"""

from __future__ import annotations

import argparse
import email.headerregistry
import json
import mimetypes
import sys
from datetime import datetime, timezone
from email import policy
from email.message import EmailMessage
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mail_frontmatter  # noqa: E402
import mail_ics  # noqa: E402
import mail_render  # noqa: E402

CID_DOMAIN = "local"  # deliberately neutral: this project may be renamed


class MessageIDListHeader(email.headerregistry.UnstructuredHeader):
    """One or more `<id>` tokens, folded only at the spaces between them.

    Left unregistered, `EmailPolicy` treats such a header as unstructured prose and folds a
    token too long for one line by RFC 2047-encoding it - `<abc@x>` comes out as
    `=3Cabc=40x=3E`, which no client can thread on. `MessageIDHeader` avoids that but holds
    a single id, so it would silently drop the rest of a References chain.
    """

    def fold(self, *, policy: email.policy.Policy) -> str:
        name = self.name
        lines: list[str] = []
        current = ""
        for token in str(self).split():
            candidate = f"{current} {token}" if current else token
            if current and len(name) + 2 + len(candidate) > policy.max_line_length:
                lines.append(current)
                current = token
            else:
                current = candidate
        lines.append(current)
        # A single id can exceed the line length and has nowhere to fold; that is legal
        # (RFC 5322 allows 998 octets) and far better than mangling it.
        # fold() returns the whole header, trailing line separator included.
        return f"{name}: " + (policy.linesep + " ").join(lines) + policy.linesep


def _threading_registry() -> email.headerregistry.HeaderRegistry:
    """The default header registry, with the threading headers folding as id lists."""
    registry = email.headerregistry.HeaderRegistry()
    registry.map_to_type("in-reply-to", MessageIDListHeader)
    registry.map_to_type("references", MessageIDListHeader)
    return registry


SMTP = policy.SMTP.clone(header_factory=_threading_registry())
# CRLF line endings, which Outlook expects, plus the threading headers above.


class BuildError(RuntimeError):
    """A problem that must stop the build rather than produce a wrong file."""


def _guess_type(path: Path) -> tuple[str, str]:
    guessed, _ = mimetypes.guess_type(path.name)
    if not guessed or "/" not in guessed:
        return "application", "octet-stream"
    maintype, subtype = guessed.split("/", 1)
    return maintype, subtype


def _read_bytes(path: Path, what: str) -> bytes:
    if not path.is_file():
        raise BuildError(f"{what} not found: {path}")
    return path.read_bytes()


def resolve_images(paths: list[str], base_dir: Path) -> list[tuple[str, str, Path]]:
    """Map body image paths to CIDs, in order. Returns [(body_path, cid, file)].

    The CID is counter-based, never derived from the basename: Outlook reuses `image.png`
    for every inline image, which silently collides on extraction.
    """
    resolved: list[tuple[str, str, Path]] = []
    for index, raw in enumerate(paths, start=1):
        path = (base_dir / raw).resolve()
        if not path.is_file():
            raise BuildError(f"image referenced in the body not found: {path}")
        resolved.append((raw, f"img-{index}@{CID_DOMAIN}", path))
    return resolved


def build_eml(
    doc: mail_frontmatter.ParsedDoc,
    base_dir: Path,
    *,
    text_only: bool = False,
    from_addr: str = "",
    date_header: str = "",
    draft: bool = False,
) -> tuple[bytes, list[str]]:
    """Assemble the message. Returns its bytes and any warnings."""
    warnings: list[str] = []
    to = doc.addresses("to")
    if not to:
        raise BuildError("frontmatter has no 'to:' address - there is nowhere to send this")

    blocks = mail_render.parse_blocks(doc.body)
    images = resolve_images(mail_render.collect_image_paths(blocks), base_dir)
    cid_for = {body_path: cid for body_path, cid, _ in images}

    html, warnings_from_html = mail_render.render_html(blocks, cid_for)
    warnings.extend(warnings_from_html)
    plain = mail_render.render_plain(blocks)

    if text_only:
        message = EmailMessage(policy=SMTP)
        message.set_content(plain)
    else:
        alternative = EmailMessage(policy=SMTP)
        alternative.set_content(plain)
        alternative.add_alternative(html, subtype="html")
        if images:
            message = EmailMessage(policy=SMTP)
            # RFC 2387 makes the FIRST part of a `related` the root, so the alternative
            # must be attached before the images - an image first renders as the body.
            message.make_related()
            message.attach(alternative)
            for _body_path, cid, path in images:
                maintype, subtype = _guess_type(path)
                message.add_related(
                    _read_bytes(path, "inline image"),
                    maintype=maintype,
                    subtype=subtype,
                    cid=f"<{cid}>",
                    filename=path.name,
                    disposition="inline",
                )
        else:
            message = alternative

    subject = doc.get("subject")
    if subject:
        message["Subject"] = subject
    message["To"] = ", ".join(to)
    for header, key in (("Cc", "cc"), ("Bcc", "bcc"), ("Reply-To", "reply-to")):
        values = doc.addresses(key)
        if values:
            message[header] = ", ".join(values)
    if doc.addresses("bcc"):
        warnings.append(
            "bcc: is set - safe in Outlook, which strips it on send, but this .eml carries "
            "the blind list in the clear for anything else that sends it"
        )
    # `from:` is an ordinary address key in the frontmatter; --from overrides it. In
    # received style this is the address Reply will answer, so it is not cosmetic.
    from_frontmatter = doc.addresses("from")
    from_header = from_addr or (from_frontmatter[0] if from_frontmatter else "")
    if from_header:
        message["From"] = from_header
    if date_header:
        message["Date"] = date_header
    # Date and Message-ID are left to the client unless the frontmatter names them: a new
    # message should get a new id, and a From Outlook cannot resolve makes Send fail with
    # "You can't send a message on behalf of this user".

    in_reply_to = doc.message_ids("in-reply-to")
    references = doc.message_ids("references") or in_reply_to

    own_ids = doc.message_ids("message-id")
    if own_ids:
        # Setting the id that a client would otherwise generate is what makes a file stand
        # in for a specific message - the basis of a reply-ready scaffold.
        message["Message-ID"] = own_ids[0]
        if len(own_ids) > 1:
            warnings.append(f"message-id: takes one id; using {own_ids[0]}")
        if own_ids[0] in in_reply_to:
            warnings.append(
                "message-id: is also in in-reply-to: - the message would be a reply to "
                "itself; set one or the other"
            )

    if in_reply_to:
        message["In-Reply-To"] = " ".join(in_reply_to)
    if references:
        message["References"] = " ".join(references)
    if references and not in_reply_to:
        warnings.append(
            "references: is set without in-reply-to: - Outlook threads on In-Reply-To, so "
            "this may still arrive as a new conversation"
        )

    if draft:
        # `X-Unsent: 1` makes Outlook open the file as an editable draft with a Send
        # button - and therefore with no Reply button, since it is already a reply.
        message["X-Unsent"] = "1"
    elif not from_header:
        warnings.append(
            "no from: address - Outlook will show no sender on this received-style message, "
            "and Reply will have no address to answer; set from: or pass --from"
        )

    attachments = doc.paths("attach")
    for raw in attachments:
        path = (base_dir / raw).resolve()
        data = _read_bytes(path, "attachment")
        maintype, subtype = _guess_type(path)
        message.add_attachment(data, maintype=maintype, subtype=subtype, filename=path.name)
        if any(path == image for _body_path, _cid, image in images):
            warnings.append(f"{path.name} is both inline and attached - it will appear twice")

    return message.as_bytes(), warnings


def build_calendar(
    doc: mail_frontmatter.ParsedDoc, base_dir: Path, *, now: datetime
) -> tuple[bytes | None, list[str]]:
    event = doc.event()
    if not event.get("title") or not event.get("start"):
        return None, []
    slug = base_dir.name
    text, warnings = mail_ics.build_ics(event=event, slug=slug, now=now)
    return text.encode("utf-8"), warnings


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="build_mail.py",
        description="Build an importable .eml and/or .ics from a reply draft.",
    )
    parser.add_argument("draft", type=Path, help="the markdown draft (e.g. final.md)")
    parser.add_argument("--out", type=Path, default=None, help="output directory")
    parser.add_argument("--eml", action="store_true", help="build only the .eml")
    parser.add_argument("--ics", action="store_true", help="build only the .ics")
    parser.add_argument(
        "--text-only", action="store_true", help="plain-text .eml with no HTML alternative"
    )
    parser.add_argument("--name", default=None, help="output stem (default: round directory name)")
    parser.add_argument(
        "--eol",
        choices=("crlf", "lf"),
        default="crlf",
        help="line endings; crlf (default) is what Outlook expects",
    )
    parser.add_argument("--from", dest="from_addr", default="", help="set a From header")
    parser.add_argument("--date", dest="date_header", default="", help="set a Date header")
    # Named --as-draft, not --draft: the positional `draft` already owns that dest, and
    # argparse would let the two silently clobber each other.
    parser.add_argument(
        "--as-draft",
        dest="as_draft",
        action="store_true",
        help="mark the .eml X-Unsent: 1 so Outlook opens it as a compose window with Send",
    )
    parser.add_argument("--strict", action="store_true", help="treat warnings as failure")
    parser.add_argument("--json", action="store_true", help="machine-readable result on stdout")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    draft: Path = args.draft
    if not draft.is_file():
        print(f"build_mail: no such draft: {draft}", file=sys.stderr)
        return 1

    base_dir = draft.resolve().parent
    stem = args.name or base_dir.name
    out_dir = (args.out or base_dir)
    do_eml = not args.ics
    do_ics = not args.eml
    now = datetime.now(timezone.utc)

    try:
        source = draft.read_text(encoding="utf-8")
        doc = mail_frontmatter.parse(source)
        warnings = list(doc.warnings)

        written: dict[str, str] = {}
        if do_eml:
            data, eml_warnings = build_eml(
                doc,
                base_dir,
                text_only=args.text_only,
                from_addr=args.from_addr,
                date_header=args.date_header,
                draft=args.as_draft,
            )
            warnings.extend(eml_warnings)
            if args.eol == "lf":
                data = data.replace(b"\r\n", b"\n")
                warnings.append("--eol lf: Outlook may garble LF-only files")
            out_dir.mkdir(parents=True, exist_ok=True)
            target = out_dir / f"{stem}.eml"
            target.write_bytes(data)
            written["eml"] = str(target)

        if do_ics:
            data, ics_warnings = build_calendar(doc, base_dir, now=now)
            warnings.extend(ics_warnings)
            if data is not None:
                out_dir.mkdir(parents=True, exist_ok=True)
                target = out_dir / f"{stem}.ics"
                target.write_bytes(data)
                written["ics"] = str(target)
    except (BuildError, mail_ics.EventError) as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}))
        else:
            print(f"build_mail: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({"ok": True, "written": written, "warnings": warnings}))
    else:
        for kind, path in written.items():
            print(f"{kind}: {path}")
        if not written:
            print("build_mail: nothing to build (no frontmatter, or no event.* keys)")
        for warning in warnings:
            print(f"  warning: {warning}", file=sys.stderr)

    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
