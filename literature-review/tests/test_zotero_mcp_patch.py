"""Tests for scripts/zotero_mcp_patch — the pyzotero attachment_both fix.

The bug: pyzotero puts the full path into the attachment template's
`filename`; the Zotero web API rejects directory paths in stored-file
filenames, the upload lands in `failure`, and zotero-mcp-server ignores it.
The patch must (1) send basename-only filenames, (2) pass the directory via
Zupload's basedir, (3) raise when any upload fails.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

pytest.importorskip("pyzotero")

import pyzotero._upload as upload_mod  # noqa: E402
import zotero_mcp_patch  # noqa: E402
from pyzotero._client import Zotero  # noqa: E402


class FakeZupload:
    """Records constructor args; returns a canned upload() result."""

    instances: list["FakeZupload"] = []
    result = {"success": [], "failure": [], "unchanged": []}

    def __init__(self, zinst, payload, parentid, basedir=None):
        self.payload = payload
        self.parentid = parentid
        self.basedir = basedir
        FakeZupload.instances.append(self)

    def upload(self):
        if not FakeZupload.result["success"] and not FakeZupload.result["failure"]:
            # default: everything succeeds
            return {"success": self.payload, "failure": [], "unchanged": []}
        return FakeZupload.result


def _client():
    z = Zotero.__new__(Zotero)  # skip __init__ (no network)
    z._attachment_template = MagicMock(
        return_value={"itemType": "attachment", "linkMode": "imported_file"}
    )
    return z


@pytest.fixture(autouse=True)
def _patch(monkeypatch):
    FakeZupload.instances = []
    FakeZupload.result = {"success": [], "failure": [], "unchanged": []}
    monkeypatch.setattr(upload_mod, "Zupload", FakeZupload)
    zotero_mcp_patch.apply()
    yield


def test_filename_is_basename_and_basedir_passed():
    z = _client()
    res = z.attachment_both([("Paper", "/some/dir/paper.pdf")], parentid="ABC123")
    up = FakeZupload.instances[0]
    assert up.payload[0]["filename"] == "paper.pdf"  # not the full path
    assert up.payload[0]["title"] == "Paper"
    assert up.basedir == "/some/dir"
    assert up.parentid == "ABC123"
    assert res["success"][0]["title"] == "Paper"


def test_files_in_different_dirs_get_separate_uploads():
    z = _client()
    z.attachment_both([("A", "/d1/a.pdf"), ("B", "/d2/b.pdf")])
    assert {u.basedir for u in FakeZupload.instances} == {"/d1", "/d2"}


def test_failure_raises_instead_of_silent_success():
    FakeZupload.result = {"success": [], "failure": [{"filename": "paper.pdf"}], "unchanged": []}
    z = _client()
    with pytest.raises(RuntimeError, match="paper.pdf"):
        z.attachment_both([("Paper", "/some/dir/paper.pdf")])
