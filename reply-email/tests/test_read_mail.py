"""Tests for the incoming-mail readers in scripts/.

Run with either:

    python -m unittest discover tests
    python -m pytest tests

The `.msg` tests build their own CFB containers: a real Outlook file cannot be committed
(AGENTS.md -> Desensitization), and an untested binary parser is the part of this package
most likely to break silently.
"""

import base64
import json
import struct
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import mail_eml  # noqa: E402  # pyright: ignore[reportMissingImports]
import mail_msg  # noqa: E402  # pyright: ignore[reportMissingImports]
import mail_read  # noqa: E402  # pyright: ignore[reportMissingImports]
import read_mail  # noqa: E402  # pyright: ignore[reportMissingImports]

SECTOR = 512
MINI = 64
MINI_CUTOFF = 4096
ENDOFCHAIN = 0xFFFFFFFE
FATSECT = 0xFFFFFFFD
FREESECT = 0xFFFFFFFF
NOSTREAM = 0xFFFFFFFF
CFB_SIGNATURE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"


# --------------------------------------------------------------------------- CFB writer


def _link(indices: list[int]) -> None:
    """Chain siblings through `right`, the shape the reader's in-order walk expects."""
    for left, right in zip(indices, indices[1:]):
        _DIR[left]["right"] = right


_DIR: list[dict] = []


def build_cfb(root_streams, substorages=None) -> bytes:
    """Assemble a minimal, spec-shaped CFB holding the given streams."""
    global _DIR
    substorages = substorages or {}
    _DIR = [{"name": "Root Entry", "type": 5, "left": -1, "right": -1, "child": -1,
             "start": -1, "size": 0, "data": None}]

    def add(name, data, obj_type=2):
        _DIR.append({"name": name, "type": obj_type, "left": -1, "right": -1, "child": -1,
                     "start": -1, "size": len(data or b""), "data": data})
        return len(_DIR) - 1

    top = [add(name, data) for name, data in root_streams]
    for storage_name, children in substorages.items():
        storage = add(storage_name, None, obj_type=1)
        kids = [add(name, data) for name, data in children]
        _DIR[storage]["child"] = kids[0] if kids else -1
        _link(kids)
        top.append(storage)
    _DIR[0]["child"] = top[0] if top else -1
    _link(top)

    # Small streams go in the mini stream; the rest take whole sectors.
    ministream = bytearray()
    for entry in _DIR:
        if entry["type"] != 2:
            continue
        entry["mini"] = entry["size"] < MINI_CUTOFF
        if entry["mini"]:
            # For a small stream the starting-sector field holds a *mini* sector index.
            entry["mini_start"] = len(ministream) // MINI
            entry["start"] = entry["mini_start"]
            ministream += entry["data"]
            ministream += b"\x00" * (-len(ministream) % MINI)

    minifat: list[int] = []
    for entry in _DIR:
        if entry["type"] == 2 and entry.get("mini"):
            count = (entry["size"] + MINI - 1) // MINI
            for step in range(count):
                last = step == count - 1
                minifat.append(ENDOFCHAIN if last else entry["mini_start"] + step + 1)

    def sectors_for(blob: bytes) -> int:
        return (len(blob) + SECTOR - 1) // SECTOR

    dir_sectors = max(1, sectors_for(bytes(len(_DIR) * 128)))
    mini_sectors = sectors_for(bytes(ministream))
    minifat_blob = b"".join(struct.pack("<I", v) for v in minifat)
    minifat_sectors = sectors_for(minifat_blob)

    regular: list[bytes] = []
    for entry in _DIR:
        if entry["type"] == 2 and not entry.get("mini"):
            padded = entry["data"] + b"\x00" * (-len(entry["data"]) % SECTOR)
            regular.append(padded)

    # Sector map: [FAT][directory][ministream][miniFAT][regular...]
    fat_sector = 0
    dir_start = 1
    next_free = dir_start + dir_sectors
    ministream_start = next_free if ministream else -1
    if ministream:
        next_free += mini_sectors
    minifat_start = next_free if minifat_blob else -1
    if minifat_blob:
        next_free += minifat_sectors
    regular_start = next_free

    total = regular_start + len(regular)
    if total > SECTOR // 4:
        raise AssertionError("test CFB needs more than one FAT sector")

    fat = [FREESECT] * (SECTOR // 4)
    fat[fat_sector] = FATSECT
    for start, count in ((dir_start, dir_sectors), (ministream_start, mini_sectors),
                         (minifat_start, minifat_sectors)):
        if start < 0 or not count:
            continue
        for step in range(count):
            fat[start + step] = ENDOFCHAIN if step == count - 1 else start + step + 1

    cursor = regular_start
    for entry, blob in zip([e for e in _DIR if e["type"] == 2 and not e.get("mini")], regular):
        count = len(blob) // SECTOR
        entry["start"] = cursor
        for step in range(count):
            fat[cursor + step] = ENDOFCHAIN if step == count - 1 else cursor + step + 1
        cursor += count

    if ministream:
        _DIR[0]["start"] = ministream_start
        _DIR[0]["size"] = len(ministream)

    directory = bytearray()
    for entry in _DIR:
        name = entry["name"].encode("utf-16-le") + b"\x00\x00"
        record = bytearray(128)
        record[0 : len(name)] = name
        struct.pack_into("<H", record, 64, len(name))
        record[66] = entry["type"]
        record[67] = 1
        struct.pack_into("<iii", record, 68, entry["left"], entry["right"], entry["child"])
        struct.pack_into("<i", record, 116, entry["start"])
        struct.pack_into("<Q", record, 120, entry["size"])
        directory += record
    directory += b"\x00" * (-len(directory) % SECTOR)

    header = bytearray(512)
    header[0:8] = CFB_SIGNATURE
    struct.pack_into("<HH", header, 24, 0x003E, 0x0003)
    struct.pack_into("<H", header, 28, 0xFFFE)
    struct.pack_into("<HH", header, 30, 9, 6)
    struct.pack_into("<I", header, 40, 0)
    struct.pack_into("<I", header, 44, 1)
    struct.pack_into("<i", header, 48, dir_start)
    struct.pack_into("<I", header, 56, MINI_CUTOFF)
    struct.pack_into("<i", header, 60, minifat_start)
    struct.pack_into("<I", header, 64, minifat_sectors)
    struct.pack_into("<i", header, 68, -2)  # no DIFAT sectors: ENDOFCHAIN
    struct.pack_into("<I", header, 72, 0)
    for slot in range(109):
        # Unsigned: an unused DIFAT slot is FREESECT, which does not fit a signed int32.
        struct.pack_into("<I", header, 76 + slot * 4, fat_sector if slot == 0 else FREESECT)

    body = bytearray()
    body += struct.pack("<%dI" % len(fat), *fat)
    body += directory
    # Each region must fill whole sectors, or every sector after it is misaligned.
    body += bytes(ministream) + b"\x00" * (-len(ministream) % SECTOR)
    body += minifat_blob + b"\x00" * (-len(minifat_blob) % SECTOR)
    for blob in regular:
        body += blob

    return bytes(header) + bytes(body)


# ------------------------------------------------------------------------ MSG builders

PT_UNICODE, PT_BINARY, PT_LONG, PT_SYSTIME = 0x001F, 0x0102, 0x0003, 0x0040


def prop_name(pid: int, kind: int) -> str:
    return "__substg1.0_%08X" % ((pid << 16) | kind)


def unicode_prop(pid: int, text: str) -> tuple[str, bytes]:
    return prop_name(pid, PT_UNICODE), text.encode("utf-16-le") + b"\x00\x00"


def binary_prop(pid: int, data: bytes) -> tuple[str, bytes]:
    return prop_name(pid, PT_BINARY), data


def props_stream(records, *, header: bool) -> tuple[str, bytes]:
    blob = bytearray(b"\x00" * 32 if header else b"")
    for kind, pid, value in records:
        blob += struct.pack("<HHI", kind, pid, 0) + value.ljust(8, b"\x00")[:8]
    return "__properties_version1.0", bytes(blob)


def filetime(moment: datetime) -> bytes:
    epoch = datetime(1601, 1, 1, tzinfo=timezone.utc)
    return struct.pack("<Q", int((moment - epoch).total_seconds() * 10_000_000))


SENT_AT = datetime(2026, 3, 4, 9, 15, tzinfo=timezone.utc)
MESSAGE_ID = "<VI3SPR01MB09268AF5C01C71A902C3CCD0A5832@eurprd09.prod.outlook.com>"

TRANSPORT = (
    "From: \"Smith, Alice\" <alice@example.com>\r\n"
    "To: Bob Jones <bob@example.com>\r\n"
    "CC: \"Carol Ng\" <carol@example.com>\r\n"
    "Subject: Operating point\r\n"
    "Date: Wed, 4 Mar 2026 09:15:00 +0000\r\n"
    f"Message-ID: {MESSAGE_ID}\r\n"
)


def sample_msg(*, transport: bool = True, attachments=None) -> bytes:
    root = [
        unicode_prop(0x0037, "Operating point"),
        unicode_prop(0x1000, "Hi Bob,\r\n\r\nPlease use 11,496 rpm.\r\n"),
        unicode_prop(0x0C1A, "Smith, Alice"),
        unicode_prop(0x0C1F, "alice@example.com"),
        props_stream([(PT_SYSTIME, 0x0039, filetime(SENT_AT))], header=True),
    ]
    if transport:
        root.append(unicode_prop(0x007D, TRANSPORT))
    return build_cfb(root, {"__attach_version1.0_#00000000": attachments or []})


def png_attachment() -> list[tuple[str, bytes]]:
    return [
        unicode_prop(0x3707, "image001.png"),
        unicode_prop(0x3703, ".png"),
        unicode_prop(0x370E, "image/png"),
        unicode_prop(0x3712, "image001.png@01DD4AB1"),
        binary_prop(0x3701, b"\x89PNG\r\n\x1a\n" + b"\x00" * 40),
        props_stream([(PT_LONG, 0x3705, struct.pack("<i", 1))], header=False),
    ]


class CfbReaderTests(unittest.TestCase):
    def test_reads_small_and_large_streams_and_substorages(self):
        small = b"small value"
        large = b"L" * 5000  # over the mini-stream cutoff, so it takes whole sectors
        blob = build_cfb(
            [("__substg1.0_0037001F", small), ("big.bin", large)],
            {"__attach_version1.0_#00000000": [("inner.bin", b"inner bytes")]},
        )
        streams, storages = mail_msg._Cfb(blob).load()

        self.assertEqual(streams["__substg1.0_0037001F"], small)
        self.assertEqual(streams["big.bin"], large)
        self.assertEqual(
            storages["__attach_version1.0_#00000000"]["inner.bin"], b"inner bytes"
        )

    def test_rejects_a_file_that_is_not_ole(self):
        with self.assertRaises(mail_read.MailReadError):
            mail_msg._Cfb(b"not a compound file at all")


class MsgExtractTests(unittest.TestCase):
    def extract(self, blob: bytes):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "message.msg"
            path.write_bytes(blob)
            return mail_msg.extract(path)

    def test_envelope_comes_from_the_transport_headers(self):
        mail = self.extract(sample_msg())

        self.assertEqual(mail.subject, "Operating point")
        self.assertEqual(str(mail.sender), "Smith, Alice <alice@example.com>")
        # The recipient table carries no PR_RECIPIENT_TYPE, so this classification is only
        # available from the stored transport headers.
        self.assertEqual([str(a) for a in mail.to], ["Bob Jones <bob@example.com>"])
        self.assertEqual([str(a) for a in mail.cc], ["Carol Ng <carol@example.com>"])

    def test_date_comes_from_the_fixed_length_property_store(self):
        mail = self.extract(sample_msg())
        self.assertEqual(mail.date, SENT_AT)

    def test_message_id_is_read_so_a_reply_can_thread(self):
        mail = self.extract(sample_msg())
        self.assertEqual(mail.message_id, MESSAGE_ID)

    def test_message_id_falls_back_to_the_mapi_property(self):
        # No transport headers at all: the id still comes from PR_INTERNET_MESSAGE_ID.
        root = [
            unicode_prop(0x0037, "No headers"),
            unicode_prop(0x1035, MESSAGE_ID),
            props_stream([(PT_SYSTIME, 0x0039, filetime(SENT_AT))], header=True),
        ]
        mail = self.extract(build_cfb(root))
        self.assertEqual(mail.message_id, MESSAGE_ID)

    def test_attachment_metadata_and_bytes(self):
        mail = self.extract(sample_msg(attachments=png_attachment()))

        self.assertEqual(len(mail.attachments), 1)
        attachment = mail.attachments[0]
        # `3703` holds ".png"; joining it to a name that already ends in .png must not
        # produce "image001.png.png".
        self.assertEqual(attachment.filename, "image001.png")
        self.assertEqual(attachment.content_type, "image/png")
        self.assertTrue(attachment.inline)  # signalled by the Content-ID, not AttachFlags
        self.assertTrue(attachment.data.startswith(b"\x89PNG"))

    def test_body_html_is_used_only_when_there_is_no_plain_part(self):
        root = [binary_prop(0x1013, b"<p>Only HTML here</p>"),
                props_stream([(PT_SYSTIME, 0x0039, filetime(SENT_AT))], header=True)]
        mail = self.extract(build_cfb(root))

        self.assertEqual(mail.body_plain, "")
        self.assertEqual(mail.body_text(), "Only HTML here")

    def test_empty_body_warns_instead_of_failing_silently(self):
        mail = self.extract(build_cfb([unicode_prop(0x0037, "Empty")]))
        self.assertTrue(any("body is empty" in w for w in mail.warnings))

    def test_reference_attachment_reports_missing_bytes(self):
        attachment = [
            unicode_prop(0x3707, "big.pdf"),
            props_stream([(PT_LONG, 0x3705, struct.pack("<i", 4))], header=False),
        ]
        mail = self.extract(sample_msg(attachments=attachment))

        self.assertTrue(mail.attachments[0].missing)
        self.assertTrue(any("bytes are not in the file" in w for w in mail.warnings))
        # It is still named in original.txt, so the gap is visible rather than silent...
        self.assertIn("big.pdf", mail_read.render_original_txt(mail))
        # ...but there is no data, so nothing is written to disk for it.
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "round"
            mail_read.write_round(mail, out)
            self.assertEqual([p.name for p in out.iterdir()], ["original.txt"])


class EmlExtractTests(unittest.TestCase):
    def write(self, raw: bytes) -> Path:
        tmp = tempfile.mkdtemp()
        path = Path(tmp) / "message.eml"
        path.write_bytes(raw)
        self.addCleanup(lambda: __import__("shutil").rmtree(tmp, ignore_errors=True))
        return path

    def test_multipart_with_cp1252_body_and_attachments(self):
        raw = (
            b"From: Alice <alice@example.com>\r\n"
            b"To: Bob <bob@example.com>\r\n"
            b"Subject: Test\r\n"
            b"Message-ID: <eml-id@example.com>\r\n"
            b'Date: Wed, 4 Mar 2026 09:15:00 +0000\r\n'
            b"MIME-Version: 1.0\r\n"
            b'Content-Type: multipart/mixed; boundary="B"\r\n\r\n'
            b"--B\r\n"
            b'Content-Type: text/plain; charset="Windows-1252"\r\n'
            b"Content-Transfer-Encoding: 8bit\r\n\r\n"
            + "Price was \u00a3478.25 for a caf\u00e9.".encode("cp1252")
            + b"\r\n--B\r\n"
            b"Content-Type: image/png\r\n"
            b"Content-Transfer-Encoding: base64\r\n"
            b"Content-ID: <image001.png>\r\n\r\n"
            + base64.b64encode(b"\x89PNG\r\n\x1a\n")
            + b"\r\n--B\r\n"
            b'Content-Type: application/pdf; name="doc.pdf"\r\n'
            b"Content-Transfer-Encoding: base64\r\n"
            b'Content-Disposition: attachment; filename="doc.pdf"\r\n\r\n'
            + base64.b64encode(b"%PDF-1.4")
            + b"\r\n--B--\r\n"
        )
        mail = mail_eml.extract(self.write(raw))

        # cp1252, not UTF-8: decoding as UTF-8 would mangle or drop this body.
        self.assertIn("\u00a3478.25", mail.body_plain)
        self.assertIn("caf\u00e9", mail.body_plain)
        self.assertEqual(str(mail.sender), "Alice <alice@example.com>")
        self.assertEqual(mail.message_id, "<eml-id@example.com>")
        names = sorted(a.filename for a in mail.attachments)
        self.assertEqual(names, ["doc.pdf", "image001.png"])
        pdf = next(a for a in mail.attachments if a.filename == "doc.pdf")
        self.assertEqual(pdf.data, b"%PDF-1.4")

    def test_body_empty_of_content_warns(self):
        raw = (
            b"From: Alice <alice@example.com>\r\n"
            b"Subject: Signature only\r\n"
            b"MIME-Version: 1.0\r\n"
            b'Content-Type: multipart/mixed; boundary="B"\r\n\r\n'
            b"--B\r\n\r\n--B--\r\n"
        )
        mail = mail_eml.extract(self.write(raw))
        self.assertTrue(any("body is empty" in w for w in mail.warnings))


class HtmlToTextTests(unittest.TestCase):
    def test_block_elements_become_paragraphs(self):
        text = mail_read.html_to_text("<div><p>One</p><p>Two</p></div>")
        self.assertEqual(text, "One\n\nTwo")

    def test_source_line_breaks_are_not_hard_wraps(self):
        # A mail client's wrapping must not reappear as a sentence break.
        text = mail_read.html_to_text("<p>a long sentence that was\r\nwrapped by the client</p>")
        self.assertEqual(text, "a long sentence that was wrapped by the client")

    def test_br_is_a_line_break_and_nbsp_does_not_create_a_paragraph(self):
        text = mail_read.html_to_text("<p>one<br>two</p><p>&nbsp;</p><p>three</p>")
        self.assertEqual(text, "one\ntwo\n\nthree")

    def test_style_and_script_are_dropped(self):
        text = mail_read.html_to_text("<style>p{color:red}</style><p>Keep</p><script>x()</script>")
        self.assertEqual(text, "Keep")

    def test_inline_image_marker_names_the_file(self):
        text = mail_read.html_to_text('<p>See</p><img src="cid:image001.jpg@01DD4AB1">')
        self.assertIn("[inline image: image001.jpg]", text)

    def test_markers_can_be_suppressed(self):
        text = mail_read.html_to_text('<img src="cid:a.jpg@x">', inline_images=False)
        self.assertEqual(text, "")


class NamingTests(unittest.TestCase):
    def test_duplicate_attachment_names_get_a_counter(self):
        used: set[str] = set()
        first = mail_read.unique_name("image.png", used)
        used.add(first)
        second = mail_read.unique_name("image.png", used)
        self.assertEqual((first, second), ("image.png", "image-2.png"))

    def test_traversal_in_an_attachment_name_is_stripped(self):
        self.assertEqual(mail_read.safe_filename("../../etc/passwd"), "passwd")
        self.assertEqual(mail_read.safe_filename(r"C:\temp\evil.exe"), "evil.exe")
        self.assertEqual(mail_read.safe_filename(""), "attachment")


class RoundWritingTests(unittest.TestCase):
    def test_writes_original_txt_and_attachments_without_clobbering(self):
        mail = mail_read.ParsedMail(
            source="x.msg",
            subject="Subject",
            sender=mail_read.Address(name="Alice", email="alice@example.com"),
            body_plain="Body text",
            attachments=[
                mail_read.Attachment("image.png", "image/png", b"one"),
                mail_read.Attachment("image.png", "image/png", b"two"),
            ],
        )
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "round"
            written = mail_read.write_round(mail, out)

            self.assertTrue((out / "original.txt").is_file())
            # Both images survive; a naive write keeps only the second.
            self.assertEqual((out / "image.png").read_bytes(), b"one")
            self.assertEqual((out / "image-2.png").read_bytes(), b"two")
            self.assertEqual(len(written), 3)

            text = (out / "original.txt").read_text(encoding="utf-8")
            self.assertIn("From: Alice <alice@example.com>", text)
            self.assertIn("Body text", text)
            self.assertIn("image.png (image/png, 3 bytes)", text)


class DispatchTests(unittest.TestCase):
    def test_msg_is_detected_by_content_not_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "no-extension-at-all"
            path.write_bytes(sample_msg())
            self.assertEqual(mail_read.read(path).subject, "Operating point")

    def test_a_msg_extension_on_a_non_ole_file_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fake.msg"
            path.write_text("just text", encoding="utf-8")
            with self.assertRaises(mail_read.MailReadError):
                mail_read.read(path)


class CommandLineTests(unittest.TestCase):
    def test_json_reports_the_envelope(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "message.msg"
            path.write_bytes(sample_msg(attachments=png_attachment()))
            import contextlib, io

            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                code = read_mail.main([str(path), "--json"])

            self.assertEqual(code, 0)
            payload = json.loads(buffer.getvalue())
            self.assertEqual(payload["subject"], "Operating point")
            self.assertEqual(payload["message_id"], MESSAGE_ID)
            self.assertEqual(payload["to"], ["Bob Jones <bob@example.com>"])
            self.assertEqual(payload["date"], "2026-03-04 09:15 UTC")
            self.assertEqual(payload["written"], [])  # nothing on disk without --out

    def test_out_writes_the_round_and_nothing_else(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "message.msg"
            source.write_bytes(sample_msg(attachments=png_attachment()))
            out = Path(tmp) / "round"

            import contextlib, io

            with contextlib.redirect_stdout(io.StringIO()):
                code = read_mail.main([str(source), "--out", str(out)])

            self.assertEqual(code, 0)
            self.assertEqual(sorted(p.name for p in out.iterdir()),
                             ["image001.png", "original.txt"])
            self.assertIn("Operating point", (out / "original.txt").read_text(encoding="utf-8"))

    def test_strict_turns_warnings_into_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "message.msg"
            path.write_bytes(build_cfb([unicode_prop(0x0037, "Empty body")]))

            import contextlib, io

            with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(read_mail.main([str(path), "--strict"]), 1)
                self.assertEqual(read_mail.main([str(path)]), 0)

    def test_unreadable_file_exits_non_zero_with_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing.msg"
            import contextlib, io

            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                code = read_mail.main([str(path), "--json"])

            self.assertEqual(code, 1)
            self.assertFalse(json.loads(buffer.getvalue())["ok"])


if __name__ == "__main__":
    unittest.main()
