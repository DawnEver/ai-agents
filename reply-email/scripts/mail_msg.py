#!/usr/bin/env python3
"""Read an Outlook `.msg` file with no third-party dependency.

A `.msg` is an OLE compound file (CFB): a small FAT filesystem holding one stream per MAPI
property, named `__substg1.0_<TAG>` where `<TAG>` is the 8-hex-digit property tag. Folders
that Outlook saves as `.msg` cannot be read by the stdlib `email` package at all, which is
why this module exists - `mail_eml.py` handles the RFC 822 case and is much simpler.

Only the properties a reply actually needs are read: envelope, body, recipients and
attachments. Everything else in the file is ignored rather than parsed.

Usage:
    from mail_msg import extract
    mail = extract(Path("incoming.msg"))
"""

from __future__ import annotations

import email
import email.parser
import email.policy
import email.utils
import struct
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from mail_read import Address, Attachment, MailReadError, ParsedMail, parse_addresses

CFB_SIGNATURE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
HEADER_SIZE = 512
DIRECTORY_ENTRY_SIZE = 128

OBJ_STORAGE = 1
OBJ_STREAM = 2
OBJ_ROOT = 5

# Property types, as they appear in the low half of a property tag.
PT_STRING8 = 0x001E
PT_UNICODE = 0x001F
PT_BINARY = 0x0102
PT_LONG = 0x0003
PT_SYSTIME = 0x0040

# Property ids.
PID_SUBJECT = 0x0037
PID_CLIENT_SUBMIT_TIME = 0x0039
PID_SENT_REPRESENTING_NAME = 0x0042
PID_SENT_REPRESENTING_EMAIL = 0x0065
PID_SENDER_NAME = 0x0C1A
PID_SENDER_EMAIL = 0x0C1F
PID_SENDER_SMTP = 0x5D01
PID_DISPLAY_TO = 0x0E04
PID_DISPLAY_CC = 0x0E03
PID_MESSAGE_DELIVERY_TIME = 0x0E06
PID_BODY = 0x1000
PID_BODY_HTML = 0x1013
PID_TRANSPORT_HEADERS = 0x007D
PID_INTERNET_MESSAGE_ID = 0x1035
PID_RECIP_TYPE = 0x0C15
PID_RECIP_SMTP = 0x39FE
PID_RECIP_DISPLAY_NAME = 0x3001
PID_RECIP_EMAIL = 0x3003
PID_ATTACH_METHOD = 0x3705
PID_ATTACH_DATA = 0x3701
PID_ATTACH_EXTENSION = 0x3703
PID_ATTACH_FILENAME = 0x3704
PID_ATTACH_LONG_FILENAME = 0x3707
PID_ATTACH_MIME = 0x370E
PID_ATTACH_CONTENT_ID = 0x3712
PID_ATTACH_FLAGS = 0x3714

ATTACH_BY_VALUE = 1
ATTACH_EMBEDDED_MSG = 5
ATTACH_INLINE_FLAG = 0x0004

PROPS_STREAM = "__properties_version1.0"
PROP_FLAG_NULL = 0x00000001

RECIP_TO, RECIP_CC, RECIP_BCC = 1, 2, 3


@dataclass
class _DirEntry:
    name: str
    obj_type: int
    left: int
    right: int
    child: int
    start: int
    size: int


class _Cfb:
    """The slice of the CFB spec a `.msg` actually uses."""

    def __init__(self, data: bytes) -> None:
        if data[:8] != CFB_SIGNATURE:
            raise MailReadError("not an OLE compound file (no CFB signature)")
        self.data = data
        self.sector_size = 1 << struct.unpack_from("<H", data, 30)[0]
        self.mini_sector_size = 1 << struct.unpack_from("<H", data, 32)[0]
        if self.sector_size < 512 or self.mini_sector_size < 8:
            raise MailReadError("implausible CFB sector sizes")
        self.directory_start = struct.unpack_from("<i", data, 48)[0]
        self.mini_cutoff = struct.unpack_from("<I", data, 56)[0] or 4096
        self.minifat_start = struct.unpack_from("<i", data, 60)[0]
        self.difat_start = struct.unpack_from("<i", data, 68)[0]
        self._read_difat()
        self._read_fat()
        self._read_directory()
        self._read_ministream()

    def _sector(self, index: int) -> bytes:
        offset = HEADER_SIZE + index * self.sector_size
        chunk = self.data[offset : offset + self.sector_size]
        if len(chunk) != self.sector_size:
            raise MailReadError("sector runs past the end of the file")
        return chunk

    def _read_difat(self) -> None:
        entries = list(struct.unpack_from("<109i", self.data, 76))
        next_sector = self.difat_start
        per_sector = self.sector_size // 4
        guard = 0
        while next_sector >= 0 and guard < 65536:
            block = struct.unpack_from("<%di" % per_sector, self._sector(next_sector), 0)
            entries.extend(block[:-1])
            next_sector = block[-1]
            guard += 1
        self.difat = [sector for sector in entries if sector >= 0]

    def _read_fat(self) -> None:
        per_sector = self.sector_size // 4
        fat: list[int] = []
        for sector in self.difat:
            fat.extend(struct.unpack_from("<%di" % per_sector, self._sector(sector), 0))
        self.fat = fat

    def _chain(self, start: int, table: list[int]) -> list[int]:
        chain: list[int] = []
        current = start
        while current >= 0:
            if current >= len(table):
                raise MailReadError("sector chain leaves the allocation table")
            chain.append(current)
            if len(chain) > 1_000_000:
                raise MailReadError("sector chain does not terminate")
            current = table[current]
        return chain

    def _read_regular(self, start: int, size: int | None = None) -> bytes:
        if start < 0:
            return b""
        raw = b"".join(self._sector(s) for s in self._chain(start, self.fat))
        return raw if size is None else raw[:size]

    def _read_mini(self, start: int, size: int) -> bytes:
        if start < 0:
            return b""
        raw = b"".join(
            self.ministream[s * self.mini_sector_size : (s + 1) * self.mini_sector_size]
            for s in self._chain(start, self.minifat)
        )
        return raw[:size]

    def _read_directory(self) -> None:
        raw = self._read_regular(self.directory_start)
        self.entries: list[_DirEntry] = []
        for offset in range(0, len(raw) - DIRECTORY_ENTRY_SIZE + 1, DIRECTORY_ENTRY_SIZE):
            entry = raw[offset : offset + DIRECTORY_ENTRY_SIZE]
            name_length = struct.unpack_from("<H", entry, 64)[0]
            name = ""
            if name_length >= 2:
                name = entry[: name_length - 2].decode("utf-16-le", "replace")
            self.entries.append(
                _DirEntry(
                    name=name,
                    obj_type=entry[66],
                    left=struct.unpack_from("<i", entry, 68)[0],
                    right=struct.unpack_from("<i", entry, 72)[0],
                    child=struct.unpack_from("<i", entry, 76)[0],
                    start=struct.unpack_from("<i", entry, 116)[0],
                    size=struct.unpack_from("<Q", entry, 120)[0],
                )
            )
        if not self.entries or self.entries[0].obj_type != OBJ_ROOT:
            raise MailReadError("CFB directory has no root entry")

    def _read_ministream(self) -> None:
        root = self.entries[0]
        self.ministream = self._read_regular(root.start, root.size)
        self.minifat: list[int] = []
        if self.minifat_start >= 0:
            raw = self._read_regular(self.minifat_start)
            self.minifat = list(struct.unpack_from("<%di" % (len(raw) // 4), raw, 0))

    def _siblings(self, index: int) -> list[int]:
        """In-order walk of a red-black sibling tree, as CFB stores directory entries."""
        found: list[int] = []
        stack: list[int] = []
        current = index
        while stack or current >= 0:
            while 0 <= current < len(self.entries):
                stack.append(current)
                current = self.entries[current].left
            if not stack:
                break
            current = stack.pop()
            found.append(current)
            current = self.entries[current].right
        return found

    def _streams_under(self, index: int) -> dict[str, bytes]:
        streams: dict[str, bytes] = {}
        for child in self._siblings(index):
            entry = self.entries[child]
            if entry.obj_type != OBJ_STREAM:
                continue
            if entry.size < self.mini_cutoff:
                streams[entry.name] = self._read_mini(entry.start, entry.size)
            else:
                streams[entry.name] = self._read_regular(entry.start, entry.size)
        return streams

    def load(self) -> tuple[dict[str, bytes], dict[str, dict[str, bytes]]]:
        """Return (root properties, {sub-storage name: its properties}).

        Both are keyed `__substg1.0_<TAG>` whether the value came from a stream of its own
        or from the fixed-length store, so callers never have to know which it was.
        """
        root = self.entries[0]
        root_streams = self._streams_under(root.child)
        properties = {
            **_fixed_properties(root_streams.get(PROPS_STREAM, b""), header=True),
            **root_streams,
        }

        storages: dict[str, dict[str, bytes]] = {}
        for index in self._siblings(root.child):
            entry = self.entries[index]
            if entry.obj_type != OBJ_STORAGE:
                continue
            child_streams = self._streams_under(entry.child)
            storages[entry.name] = {
                **_fixed_properties(child_streams.get(PROPS_STREAM, b""), header=False),
                **child_streams,
            }
        return properties, storages


def _tag(pid: int, kind: int) -> str:
    return "__substg1.0_%08X" % ((pid << 16) | kind)


def _fixed_properties(raw: bytes, *, header: bool) -> dict[str, bytes]:
    """Expand the fixed-length property store into the `__substg1.0_<TAG>` shape.

    Fixed-length values - every PT_LONG and PT_SYSTIME among them - are kept in
    `__properties_version1.0` as bare 16-byte records rather than in a stream of their
    own. Without this pass the date, the attachment method and the recipient type all
    read as absent. Only the root store carries a 32-byte header; sub-storages do not.
    """
    found: dict[str, bytes] = {}
    start = 32 if header else 0
    for offset in range(start, len(raw) - 15, 16):
        record = raw[offset : offset + 16]
        kind, pid = struct.unpack_from("<HH", record, 0)
        flags = struct.unpack_from("<I", record, 4)[0]
        if flags & PROP_FLAG_NULL:
            continue
        found["__substg1.0_%08X" % ((pid << 16) | kind)] = record[8:16]
    return found


def _unicode(streams: dict[str, bytes], pid: int) -> str:
    raw = streams.get(_tag(pid, PT_UNICODE))
    if raw is None:
        return ""
    return raw.decode("utf-16-le", "replace").rstrip("\x00").strip()


def _string8(streams: dict[str, bytes], pid: int) -> str:
    raw = streams.get(_tag(pid, PT_STRING8))
    if raw is None:
        return ""
    return raw.decode("cp1252", "replace").rstrip("\x00").strip()


def _text(streams: dict[str, bytes], pid: int) -> str:
    value = _unicode(streams, pid)
    return value if value else _string8(streams, pid)


def _binary(streams: dict[str, bytes], pid: int) -> bytes:
    raw = streams.get(_tag(pid, PT_BINARY))
    return raw or b""


def _long(streams: dict[str, bytes], pid: int) -> int | None:
    raw = streams.get(_tag(pid, PT_LONG))
    if not raw or len(raw) < 4:
        return None
    return struct.unpack_from("<i", raw, 0)[0]


def _systime(streams: dict[str, bytes], pid: int) -> datetime | None:
    raw = streams.get(_tag(pid, PT_SYSTIME))
    if not raw or len(raw) < 8:
        return None
    filetime = struct.unpack_from("<Q", raw, 0)[0]
    if not filetime:
        return None
    try:
        stamp = datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=filetime // 10)
    except OverflowError:
        return None
    # A zeroed or absurd FILETIME is corrupt metadata, not a 1601 message.
    if not 1990 <= stamp.year <= 2100:
        return None
    return stamp


def _sender(streams: dict[str, bytes]) -> Address:
    email = _text(streams, PID_SENDER_SMTP) or _text(streams, PID_SENDER_EMAIL)
    if not email:
        email = _text(streams, PID_SENT_REPRESENTING_EMAIL)
    name = _text(streams, PID_SENDER_NAME) or _text(streams, PID_SENT_REPRESENTING_NAME)
    return Address(name=name, email=email)


def _transport_headers(streams: dict[str, bytes]) -> dict[str, list[str]]:
    """Parse `PR_TRANSPORT_MESSAGE_HEADERS`, the message as it travelled on the wire.

    Worth preferring over the MAPI properties: this is the only place the file records
    which recipients were To and which were Cc. The recipient table does not carry
    `PR_RECIPIENT_TYPE` at all in a message saved by Outlook.
    """
    raw = _text(streams, PID_TRANSPORT_HEADERS)
    if not raw.strip():
        return {}
    try:
        parsed = email.parser.Parser(policy=email.policy.compat32).parsestr(
            raw, headersonly=True
        )
    except Exception:
        return {}
    wanted = ("From", "To", "Cc", "Date", "Subject", "Message-ID")
    return {name: [str(value) for value in parsed.get_all(name, [])] for name in wanted}


def _header_date(values: list[str]) -> datetime | None:
    if not values:
        return None
    try:
        return email.utils.parsedate_to_datetime(values[0])
    except (TypeError, ValueError):
        return None


def _recipients(storages: dict[str, dict[str, bytes]]) -> tuple[list[Address], list[Address]]:
    to: list[Address] = []
    cc: list[Address] = []
    for name, streams in storages.items():
        if not name.startswith("__recip_version1.0_"):
            continue
        email = _text(streams, PID_RECIP_SMTP) or _text(streams, PID_RECIP_EMAIL)
        display = _text(streams, PID_RECIP_DISPLAY_NAME)
        if not email and not display:
            continue
        address = Address(name=display, email=email)
        kind = _long(streams, PID_RECIP_TYPE)
        if kind == RECIP_CC:
            cc.append(address)
        elif kind in (None, RECIP_TO):
            to.append(address)
        # A BCC recipient in a received message is not addressed to the user, so it is
        # dropped rather than quietly promoted into the reply's To list.
    return to, cc


def _attachments(
    storages: dict[str, dict[str, bytes]], warnings: list[str]
) -> list[Attachment]:
    found: list[Attachment] = []
    for name, streams in storages.items():
        if not name.startswith("__attach_version1.0_"):
            continue
        filename = (
            _text(streams, PID_ATTACH_LONG_FILENAME)
            or _text(streams, PID_ATTACH_FILENAME)
        )
        extension = _text(streams, PID_ATTACH_EXTENSION).lstrip(".")
        if filename and extension and not filename.lower().endswith("." + extension.lower()):
            filename = f"{filename}.{extension}"
        data = _binary(streams, PID_ATTACH_DATA)
        content_type = _text(streams, PID_ATTACH_MIME)
        method = _long(streams, PID_ATTACH_METHOD)
        flags = _long(streams, PID_ATTACH_FLAGS) or 0
        # Outlook flags an embedded image either with the inline bit or - more often, and
        # as the only signal in this file - by giving it a Content-ID the body refers to.
        inline = bool(flags & ATTACH_INLINE_FLAG) or bool(_text(streams, PID_ATTACH_CONTENT_ID))

        if not filename:
            if not data:
                continue
            filename = "attachment.bin"
        if method == ATTACH_EMBEDDED_MSG:
            # The bytes are a nested .msg; keep it intact and let the caller decide.
            if not data:
                warnings.append(f"embedded message '{filename}' has no data")
                continue
            if not content_type:
                content_type = "application/vnd.ms-outlook"
            filename = filename if filename.lower().endswith(".msg") else filename + ".msg"
        elif not data:
            # By-reference attachments keep only a placeholder name in the .msg.
            warnings.append(
                f"attachment '{filename}' is referenced but its bytes are not in the file"
            )
            found.append(
                Attachment(
                    filename=filename,
                    content_type=content_type or "application/octet-stream",
                    inline=inline,
                    missing=True,
                )
            )
            continue
        found.append(
            Attachment(
                filename=filename,
                content_type=content_type or "application/octet-stream",
                data=data,
                inline=inline,
            )
        )
    return found


def extract(path: Path) -> ParsedMail:
    """Read a `.msg` file into a `ParsedMail`."""
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise MailReadError(f"cannot read {path}: {exc}") from exc

    try:
        streams, storages = _Cfb(raw).load()
    except MailReadError:
        raise
    except (struct.error, IndexError, ValueError) as exc:
        raise MailReadError(f"{path} is not a readable .msg file: {exc}") from exc

    warnings: list[str] = []
    headers = _transport_headers(streams)

    to = parse_addresses(headers.get("To", []))
    cc = parse_addresses(headers.get("Cc", []))
    if not to and not cc:
        to, cc = _recipients(storages)
    if not to and not cc:
        # No addresses anywhere: the display strings at least name who it went to, though
        # they carry no address to reply to.
        for pid, bucket in ((PID_DISPLAY_TO, to), (PID_DISPLAY_CC, cc)):
            display = _text(streams, pid)
            if display:
                bucket.extend(
                    Address(name=part.strip()) for part in display.split(";") if part.strip()
                )

    body_html = _binary(streams, PID_BODY_HTML)
    html_text = ""
    if body_html:
        for encoding in ("utf-8", "cp1252"):
            try:
                html_text = body_html.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            html_text = body_html.decode("utf-8", "replace")
            warnings.append("HTML body had no valid encoding; decoded with replacements")

    plain = _text(streams, PID_BODY)
    if not plain.strip() and not html_text.strip():
        warnings.append(
            "message body is empty - the content may live in a screenshot or attachment"
        )

    sender = _sender(streams)
    from_header = parse_addresses(headers.get("From", []))
    if from_header:
        sender = from_header[0]

    return ParsedMail(
        source=str(path),
        subject=(headers.get("Subject") or [""])[0].strip() or _text(streams, PID_SUBJECT),
        message_id=(headers.get("Message-ID") or [""])[0].strip()
        or _text(streams, PID_INTERNET_MESSAGE_ID),
        sender=sender,
        to=to,
        cc=cc,
        date=_header_date(headers.get("Date", []))
        or _systime(streams, PID_CLIENT_SUBMIT_TIME)
        or _systime(streams, PID_MESSAGE_DELIVERY_TIME),
        body_plain=plain,
        body_html=html_text,
        attachments=_attachments(storages, warnings),
        warnings=warnings,
    )
