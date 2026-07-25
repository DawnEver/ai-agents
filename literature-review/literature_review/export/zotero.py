"""Zotero sync — priority chain: MCP Bridge → SQLite → Better BibTeX CAYW.

MCP Bridge (Zotero Local MCP Bridge plugin):
    Full writes with PDF attachments while Zotero is running.
    Requires the plugin installed; discovered via MCP JSON-RPC handshake.

SQLite:
    Direct database writes with PDF attachments.
    Requires Zotero to be CLOSED.

Better BibTeX CAYW:
    Citation-only import while Zotero is running.
    No PDF attachment; items land in the inbox.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# ── Zotero schema constants (Zotero 7) ──────────────────────────────
ITEM_TYPE_JOURNAL = 22
ITEM_TYPE_CONFERENCE = 11
ITEM_TYPE_PREPRINT = 31
CREATOR_TYPE_AUTHOR = 8
CREATOR_TYPE_EDITOR = 10

F_TITLE = 1
F_ABSTRACT = 2
F_DATE = 6
F_URL = 13
F_ACCESS_DATE = 14
F_VOLUME = 19
F_PAGES = 32
F_PUBLICATION = 38
F_DOI = 59
F_ISSUE = 76

ZOTERO_DB = Path.home() / "Zotero" / "zotero.sqlite"
MCP_BRIDGE_URL = "http://127.0.0.1:23119/zotero-local-mcp-bridge/mcp"
BBT_CAYW_URL = "http://127.0.0.1:23119/better-bibtex/cayw"


# ── Per-paper result ─────────────────────────────────────────────────

@dataclass
class SyncResult:
    paper_index: int
    title: str
    backend: str          # "mcp_bridge" | "sqlite" | "cayw"
    item_key: str = ""
    attachment: bool = False
    error: str = ""


# ── Zotero MCP Bridge client ─────────────────────────────────────────

class ZoteroMCPClient:
    """Thin JSON-RPC client for the Zotero Local MCP Bridge plugin.

    The plugin exposes an MCP endpoint inside Zotero with tool-based
    access to Zotero's internal APIs.  Tool names and schemas are
    discovered dynamically — never hardcoded.
    """

    def __init__(self, url: str = MCP_BRIDGE_URL, timeout: float = 15.0):
        self._url = url
        self._timeout = timeout
        self._req_id = 0
        self._tools: dict[str, Any] = {}  # tool_name → schema

    # ── low-level JSON-RPC ───────────────────────────────────────

    def _next_id(self) -> int:
        self._req_id += 1
        return self._req_id

    def _rpc(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send a single JSON-RPC request and return the result dict."""
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params or {},
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self._url,
            data=data,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                body = json.loads(resp.read().decode("utf-8", errors="replace"))
        except urllib.error.HTTPError as e:
            raise ZoteroBridgeError(
                f"HTTP {e.code}", body=e.read().decode("utf-8", errors="replace") if e.fp else ""
            ) from e
        except urllib.error.URLError as e:
            raise ZoteroBridgeError(f"Connection failed: {e.reason}") from e
        except OSError as e:
            raise ZoteroBridgeError(f"OS error: {e}") from e

        if "error" in body:
            err = body["error"]
            raise ZoteroBridgeError(
                err.get("message", "Unknown JSON-RPC error"),
                code=err.get("code", -1),
            )
        return body.get("result", body)

    # ── lifecycle ────────────────────────────────────────────────

    def available(self) -> bool:
        """Check whether the MCP bridge endpoint is reachable."""
        try:
            # A minimal initialize call — the bridge should respond
            self._rpc("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "lit-review", "version": "1.0"},
            })
            return True
        except ZoteroBridgeError:
            return False
        except Exception:
            return False

    def initialize(self) -> None:
        """Perform the full MCP handshake: initialize → initialized notification."""
        result = self._rpc("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "lit-review", "version": "1.0"},
        })
        # The server may return capabilities and serverInfo
        server_info = result.get("serverInfo", {})
        if server_info:
            print(f"    MCP server: {server_info.get('name', '?')} v{server_info.get('version', '?')}")
        # Send initialized notification (no response expected)
        try:
            self._rpc("notifications/initialized", {})
        except Exception:
            pass  # notification may not return a result

    def list_tools(self) -> dict[str, Any]:
        """Discover available tools. Returns {tool_name: schema, ...}."""
        result = self._rpc("tools/list", {})
        tools: dict[str, Any] = {}
        for t in result.get("tools", []):
            name = t.get("name", "")
            if name:
                tools[name] = t
                print(f"    MCP tool: {name} — {t.get('description', '')[:80]}")
        self._tools = tools
        return tools

    # ── high-level operations (tool names discovered at runtime) ───

    def _find_tool(self, *candidates: str) -> str | None:
        """Return the first tool name from *candidates* that exists, or None."""
        for name in candidates:
            if name in self._tools:
                return name
        # Fuzzy match — any tool containing a keyword
        for name in self._tools:
            for c in candidates:
                if c.lower() in name.lower():
                    return name
        return None

    def _call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a named tool with arguments."""
        return self._rpc("tools/call", {
            "name": tool_name,
            "arguments": arguments,
        })

    def import_pdf(self, pdf_path: Path, metadata: dict[str, Any]) -> str | None:
        """Import a PDF into Zotero, letting Zotero extract metadata.

        Returns the Zotero item key on success, or None.
        """
        tool = self._find_tool("import_pdf", "import_file", "importFromFile", "add_attachment")
        if not tool:
            raise ZoteroBridgeError("No PDF import tool found in MCP bridge")

        abs_path = str(pdf_path.resolve())
        result = self._call_tool(tool, {"path": abs_path, **metadata})
        # Try common key field names in the response
        key = (
            result.get("key")
            or result.get("itemKey")
            or result.get("item_key")
            or (result.get("content", [{}])[0].get("key") if isinstance(result.get("content"), list) else None)
        )
        return str(key) if key else None

    def create_item(self, metadata: dict[str, Any]) -> str | None:
        """Create a Zotero item from metadata. Returns the item key or None."""
        tool = self._find_tool("create_item", "createItem", "write_item", "add_item")
        if not tool:
            raise ZoteroBridgeError("No item creation tool found in MCP bridge")

        result = self._call_tool(tool, metadata)
        key = (
            result.get("key")
            or result.get("itemKey")
            or result.get("item_key")
        )
        return str(key) if key else None

    def add_to_collection(self, item_key: str, collection_name: str) -> bool:
        """Add an item to a named collection. Creates the collection if needed."""
        tool = self._find_tool(
            "add_to_collection", "addToCollection", "collection_add",
            "move_to_collection", "set_collection",
        )
        if not tool:
            raise ZoteroBridgeError("No collection tool found in MCP bridge")

        self._call_tool(tool, {"itemKey": item_key, "collection": collection_name})
        return True


class ZoteroBridgeError(Exception):
    """Error from the Zotero MCP bridge."""

    def __init__(self, message: str, code: int = -1, body: str = ""):
        super().__init__(f"[Zotero MCP] {message}")
        self.code = code
        self.body = body


# ── SQLite helpers (unchanged from original) ─────────────────────────

def _zotero_key() -> str:
    raw = uuid.uuid4().hex.encode()
    return hashlib.md5(raw).hexdigest()[:8].upper()


def _ensure_value(conn: sqlite3.Connection, value: str) -> int:
    c = conn.cursor()
    c.execute("SELECT valueID FROM itemDataValues WHERE value=?", (value,))
    row = c.fetchone()
    if row:
        return row[0]
    c.execute("INSERT INTO itemDataValues (value) VALUES (?)", (value,))
    return c.lastrowid


def _set_field(conn: sqlite3.Connection, item_id: int, field_id: int, value: str) -> None:
    if not value:
        return
    c = conn.cursor()
    vid = _ensure_value(conn, value)
    c.execute(
        "INSERT INTO itemData (itemID, fieldID, valueID) VALUES (?, ?, ?)",
        (item_id, field_id, vid),
    )


def _add_creator(
    conn: sqlite3.Connection, item_id: int, full_name: str,
    order_index: int, creator_type: int = CREATOR_TYPE_AUTHOR,
) -> None:
    name = full_name.strip()
    if not name:
        return
    if "," in name:
        last, _, first = name.partition(",")
        last = last.strip(); first = first.strip()
    else:
        parts = name.split()
        first = " ".join(parts[:-1]) if len(parts) >= 2 else ""
        last = parts[-1] if parts else name
    c = conn.cursor()
    c.execute("SELECT creatorID FROM creators WHERE firstName=? AND lastName=?", (first, last))
    row = c.fetchone()
    creator_id = row[0] if row else (
        c.execute("INSERT INTO creators (firstName, lastName) VALUES (?, ?)", (first, last))
        or c.lastrowid
    )
    c.execute(
        "INSERT INTO itemCreators (itemID, creatorID, creatorTypeID, orderIndex) VALUES (?, ?, ?, ?)",
        (item_id, creator_id, creator_type, order_index),
    )


def _storage_dir() -> Path:
    import glob as _glob
    profile_dir = ZOTERO_DB.parent
    profiles = _glob.glob(str(profile_dir / "Profiles" / "*"))
    if profiles:
        return Path(profiles[0]) / "storage"
    storage = profile_dir / "storage"
    if storage.exists():
        return storage
    raise FileNotFoundError("Cannot find Zotero storage directory")


def add_paper(
    conn: sqlite3.Connection, *, title: str,
    authors: list[str] | None = None, abstract: str = "",
    year: int | None = None, venue: str = "", doi: str = "",
    url: str = "", pages: str = "", volume: str = "", issue: str = "",
    pdf_path: str | None = None,
    item_type: int = ITEM_TYPE_JOURNAL, library_id: int = 1,
) -> tuple[int, str]:
    """Insert a paper into Zotero, optionally attaching a PDF.

    Returns (itemID, zotero_key).
    """
    c = conn.cursor()
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    zkey = _zotero_key()
    c.execute(
        """INSERT INTO items (itemTypeID, key, libraryID, dateAdded, dateModified,
           clientDateModified, version) VALUES (?, ?, ?, ?, ?, ?, 0)""",
        (item_type, zkey, library_id, now, now, now),
    )
    item_id = c.lastrowid
    for fid, val in [
        (F_TITLE, title), (F_ABSTRACT, abstract),
        (F_DATE, str(year) if year else ""), (F_PUBLICATION, venue),
        (F_DOI, doi), (F_URL, url), (F_PAGES, pages),
        (F_VOLUME, volume), (F_ISSUE, issue), (F_ACCESS_DATE, now[:10]),
    ]:
        _set_field(conn, item_id, fid, val)
    if authors:
        for i, author in enumerate(authors):
            _add_creator(conn, item_id, author, i)
    if pdf_path:
        pdf_file = Path(pdf_path)
        if pdf_file.exists():
            pdf_key = _zotero_key()
            c.execute(
                """INSERT INTO items (itemTypeID, key, libraryID, dateAdded, dateModified,
                   clientDateModified, version) VALUES (?, ?, ?, ?, ?, ?, 0)""",
                (3, pdf_key, library_id, now, now, now),
            )
            attach_id = c.lastrowid
            safe_name = pdf_file.name
            c.execute(
                """INSERT INTO itemAttachments
                   (itemID, parentItemID, linkMode, contentType, path, syncState)
                   VALUES (?, ?, 0, 'application/pdf', ?, 0)""",
                (attach_id, item_id, f"storage:{safe_name}"),
            )
            _set_field(conn, attach_id, 1, safe_name)
            storage = _storage_dir() / pdf_key
            storage.mkdir(parents=True, exist_ok=True)
            dest = storage / safe_name
            if not dest.exists():
                import shutil; shutil.copy2(pdf_file, dest)
    return item_id, zkey


def add_to_collection(conn: sqlite3.Connection, item_id: int, collection_id: int) -> None:
    c = conn.cursor()
    c.execute("SELECT MAX(orderIndex) FROM collectionItems WHERE collectionID=?", (collection_id,))
    row = c.fetchone()
    c.execute(
        "INSERT INTO collectionItems (collectionID, itemID, orderIndex) VALUES (?, ?, ?)",
        (collection_id, item_id, (row[0] or 0) + 1),
    )


def find_or_create_collection(conn: sqlite3.Connection, name: str, library_id: int = 1) -> int:
    c = conn.cursor()
    c.execute(
        "SELECT collectionID FROM collections WHERE collectionName=? AND libraryID=?",
        (name, library_id),
    )
    row = c.fetchone()
    if row:
        return row[0]
    c.execute(
        "INSERT INTO collections (collectionName, libraryID, version) VALUES (?, ?, 0)",
        (name, library_id),
    )
    return c.lastrowid


# ── Better BibTeX CAYW ────────────────────────────────────────────────

def _paper_to_bibtex(paper: dict[str, Any], cite_key: str) -> str:
    authors = paper.get("authors", [])
    author_str = " and ".join(authors) if authors else "Unknown"
    lines = [f"@article{{{cite_key},"]
    lines.append(f"  title = {{{paper.get('title', '')}}},")
    lines.append(f"  author = {{{author_str}}},")
    if paper.get("year"):
        lines.append(f"  year = {{{paper['year']}}},")
    if paper.get("venue"):
        lines.append(f"  journal = {{{paper['venue']}}},")
    if paper.get("doi"):
        lines.append(f"  doi = {{{paper['doi']}}},")
    if paper.get("url"):
        lines.append(f"  url = {{{paper['url']}}},")
    abstract = paper.get("abstract", "")
    if abstract:
        lines.append(f"  abstract = {{{abstract[:500]}}},")
    lines.append("}")
    return "\n".join(lines)


def _cayw_import(bibtex: str) -> bool:
    req = urllib.request.Request(
        f"{BBT_CAYW_URL}?progid=lit-review",
        data=bibtex.encode("utf-8"),
        headers={"Content-Type": "text/plain"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        print(f"    CAYW HTTP {e.code}: {body[:120]}")
        return False
    except OSError:
        return False


def _cayw_available() -> bool:
    try:
        req = urllib.request.Request(BBT_CAYW_URL, method="HEAD")
        with urllib.request.urlopen(req, timeout=2):
            return True
    except urllib.error.HTTPError:
        try:
            minimal = "@article{_test,title={_test},author={Test}}"
            req = urllib.request.Request(
                f"{BBT_CAYW_URL}?progid=lit-review",
                data=minimal.encode("utf-8"),
                headers={"Content-Type": "text/plain"}, method="POST",
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except urllib.error.HTTPError:
            return True
        except OSError:
            return False
    except OSError:
        return False


def _sqlite_available() -> bool:
    try:
        conn = sqlite3.connect(str(ZOTERO_DB))
        conn.execute("SELECT 1 FROM items LIMIT 1")
        conn.close()
        return True
    except sqlite3.OperationalError:
        return False


# ── Duplicate detection ───────────────────────────────────────────────

def _dedup_key(paper: dict[str, Any]) -> str | None:
    """Return a stable dedup key: DOI first, then arXiv/PMID, then title+year."""
    doi = str(paper.get("doi", "")).strip().lower()
    if doi:
        return f"doi:{doi}"
    arxiv = str((paper.get("provider_raw") or {}).get("arxiv_id", "")).strip()
    if arxiv:
        return f"arxiv:{arxiv}"
    title = str(paper.get("title", "")).strip().lower()
    year = paper.get("year", "")
    if title:
        return f"title:{title[:80]}|{year}"
    return None


def _validate_pdf(pdf_path: str | None, expected_sha256: str | None = None) -> bool:
    """Check that the PDF exists, is a valid PDF, and optionally matches SHA-256."""
    if not pdf_path:
        return False
    p = Path(pdf_path)
    if not p.is_file():
        return False
    if p.stat().st_size < 100:
        return False
    with p.open("rb") as f:
        if f.read(4) != b"%PDF":
            return False
    if expected_sha256:
        actual = hashlib.sha256(p.read_bytes()).hexdigest()
        if actual != expected_sha256:
            return False
    return True


# ── Main sync ─────────────────────────────────────────────────────────

def sync_papers(
    papers: list[dict[str, Any]],
    collection: str = "Engineering",
    db_path: Path | None = None,
) -> list[SyncResult]:
    """Sync papers into Zotero with the best available backend.

    Priority chain:
      1. MCP Bridge  (Zotero running, full write + PDF)
      2. SQLite       (Zotero closed, full write + PDF)
      3. CAYW         (Zotero running, citation only, no PDF)

    Args:
        papers: List of dicts with: title, authors, abstract, year, venue, doi, url,
                and optionally pdf_path, pdf_sha256, provider_raw.arxiv_id
        collection: Target Zotero collection name (default "Engineering")
        db_path: Override path to zotero.sqlite

    Returns:
        List of SyncResult, one per paper, with backend, item_key, attachment, error.
    """
    results: list[SyncResult] = []
    seen: set[str] = set()

    # ── 1. Try MCP Bridge ──────────────────────────────────────
    mcp = ZoteroMCPClient()
    mcp_ok = mcp.available()
    if mcp_ok:
        print("Backend: MCP Bridge (Zotero running, full write + PDF)\n")
        try:
            mcp.initialize()
            tools = mcp.list_tools()
            has_import = mcp._find_tool("import_pdf", "import_file", "importFromFile") is not None
            has_create = mcp._find_tool("create_item", "createItem", "write_item") is not None
            has_coll   = mcp._find_tool("add_to_collection", "addToCollection", "move_to_collection") is not None

            for i, p in enumerate(papers):
                title = str(p.get("title", ""))[:80]
                dk = _dedup_key(p)
                # Duplicate check
                if dk and dk in seen:
                    results.append(SyncResult(i, title, "mcp_bridge", error="duplicate (skipped)"))
                    continue
                if dk:
                    seen.add(dk)

                pdf_path = p.get("pdf_path", "")
                pdf_ok = _validate_pdf(pdf_path, p.get("pdf_sha256"))
                pdf_abs = str(Path(pdf_path).resolve()) if pdf_ok else ""

                try:
                    item_key: str | None = None
                    has_attachment = False

                    if pdf_ok and has_import:
                        # Import PDF with auto metadata recognition
                        item_key = mcp.import_pdf(Path(pdf_abs), {
                            "title": p.get("title", ""),
                            "creators": [
                                {"creatorType": "author", "name": a}
                                for a in (p.get("authors") or [])
                            ],
                            "date": str(p.get("year", "")),
                            "DOI": p.get("doi", ""),
                        })
                        has_attachment = True
                    elif has_create:
                        item_key = mcp.create_item({
                            "title": p.get("title", ""),
                            "creators": [
                                {"creatorType": "author", "name": a}
                                for a in (p.get("authors") or [])
                            ],
                            "date": str(p.get("year", "")),
                            "publicationTitle": p.get("venue", ""),
                            "DOI": p.get("doi", ""),
                            "url": p.get("url", ""),
                            "abstractNote": p.get("abstract", ""),
                        })

                    if item_key and has_coll:
                        try:
                            mcp.add_to_collection(item_key, collection)
                        except ZoteroBridgeError:
                            pass  # collection assignment is best-effort

                    if item_key:
                        print(f"  ✓ {title}")
                        results.append(SyncResult(
                            i, title, "mcp_bridge",
                            item_key=item_key, attachment=has_attachment,
                        ))
                    else:
                        results.append(SyncResult(
                            i, title, "mcp_bridge",
                            error="import returned no item key",
                        ))
                except ZoteroBridgeError as e:
                    print(f"  ✗ {title} — MCP error: {e}")
                    results.append(SyncResult(i, title, "mcp_bridge", error=str(e)))
                # Never auto-retry — duplicate detection must run first

            return results
        except ZoteroBridgeError as e:
            print(f"  MCP bridge error: {e} — falling back")
            mcp_ok = False
        except Exception as e:
            print(f"  MCP bridge unexpected error: {e} — falling back")
            mcp_ok = False

    # ── 2. Try SQLite (Zotero closed) ──────────────────────────
    if not mcp_ok and _sqlite_available():
        print("Backend: SQLite (Zotero closed, full write + PDF)\n")
        db = Path(db_path) if db_path else ZOTERO_DB
        conn = sqlite3.connect(str(db))
        try:
            coll_id = find_or_create_collection(conn, collection)
            for i, p in enumerate(papers):
                title = str(p.get("title", ""))[:80]
                dk = _dedup_key(p)
                if dk and dk in seen:
                    results.append(SyncResult(i, title, "sqlite", error="duplicate (skipped)"))
                    continue
                if dk:
                    seen.add(dk)

                pdf_path = p.get("pdf_path", "")
                pdf_ok = _validate_pdf(pdf_path, p.get("pdf_sha256"))

                try:
                    item_id, zkey = add_paper(
                        conn,
                        title=p.get("title", ""),
                        authors=p.get("authors", []),
                        abstract=p.get("abstract", ""),
                        year=p.get("year"),
                        venue=p.get("venue", ""),
                        doi=p.get("doi", ""),
                        url=p.get("url", ""),
                        pdf_path=pdf_path if pdf_ok else None,
                    )
                    add_to_collection(conn, item_id, coll_id)
                    print(f"  ✓ {title}")
                    results.append(SyncResult(
                        i, title, "sqlite",
                        item_key=zkey, attachment=pdf_ok,
                    ))
                except Exception as e:
                    print(f"  ✗ {title} — {e}")
                    results.append(SyncResult(i, title, "sqlite", error=str(e)))
        finally:
            conn.commit()
            conn.close()
        return results

    # ── 3. Fall back to CAYW (citation only) ───────────────────
    if _cayw_available():
        print("Backend: Better BibTeX CAYW (Zotero running, citation only, no PDF)\n")
        for i, p in enumerate(papers):
            title = str(p.get("title", ""))[:80]
            dk = _dedup_key(p)
            if dk and dk in seen:
                results.append(SyncResult(i, title, "cayw", error="duplicate (skipped)"))
                continue
            if dk:
                seen.add(dk)
            cite_key = f"CHP-{p.get('year', '?')}-{i+1:02d}"
            if _cayw_import(_paper_to_bibtex(p, cite_key)):
                print(f"  ✓ {title}")
                results.append(SyncResult(i, title, "cayw", attachment=False))
            else:
                print(f"  ✗ {title}")
                results.append(SyncResult(i, title, "cayw", error="CAYW import failed"))
        print(f"\nNote: items imported to Zotero inbox. Drag to '{collection}' collection.")
        return results

    # ── Nothing available ──────────────────────────────────────
    raise RuntimeError(
        "No Zotero backend available.\n"
        "Options:\n"
        "  1. Install Zotero Local MCP Bridge plugin (recommended — full write while running)\n"
        "  2. Close Zotero for SQLite sync\n"
        "  3. Install Better BibTeX for Zotero (citation-only import)"
    )
