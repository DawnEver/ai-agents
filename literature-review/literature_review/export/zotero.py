"""Zotero sync — two methods, auto-detected:

1. Better BibTeX CAYW (Zotero running, no close needed) — preferred
2. Direct SQLite insertion (Zotero closed) — fallback

The sync_papers() function tries CAYW first, falls back to SQLite.
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

# ── Zotero schema constants (Zotero 7) ──────────────────────────────
ITEM_TYPE_JOURNAL = 22
ITEM_TYPE_CONFERENCE = 11
ITEM_TYPE_PREPRINT = 31
CREATOR_TYPE_AUTHOR = 8
CREATOR_TYPE_EDITOR = 10

# Field IDs
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
F_EXTRA = 39
F_LIBRARY_CATALOG = 34

ZOTERO_DB = Path.home() / "Zotero" / "zotero.sqlite"


def _zotero_key() -> str:
    """Generate a Zotero-style 8-char item key."""
    raw = uuid.uuid4().hex.encode()
    return hashlib.md5(raw).hexdigest()[:8].upper()


def _ensure_value(conn: sqlite3.Connection, value: str) -> int:
    """Get or create an itemDataValues row, return its valueID."""
    c = conn.cursor()
    c.execute("SELECT valueID FROM itemDataValues WHERE value=?", (value,))
    row = c.fetchone()
    if row:
        return row[0]
    c.execute("INSERT INTO itemDataValues (value) VALUES (?)", (value,))
    return c.lastrowid


def _set_field(conn: sqlite3.Connection, item_id: int, field_id: int, value: str) -> None:
    """Set a field on an item."""
    if not value:
        return
    c = conn.cursor()
    vid = _ensure_value(conn, value)
    c.execute(
        "INSERT INTO itemData (itemID, fieldID, valueID) VALUES (?, ?, ?)",
        (item_id, field_id, vid),
    )


def _add_creator(
    conn: sqlite3.Connection,
    item_id: int,
    full_name: str,
    order_index: int,
    creator_type: int = CREATOR_TYPE_AUTHOR,
) -> None:
    """Add a creator (author/editor) to an item. Parses 'Last, First' or 'First Last'."""
    name = full_name.strip()
    if not name:
        return
    # Try "Last, First" format
    if "," in name:
        last, _, first = name.partition(",")
        last = last.strip()
        first = first.strip()
    else:
        parts = name.split()
        if len(parts) >= 2:
            first = " ".join(parts[:-1])
            last = parts[-1]
        else:
            first = ""
            last = name

    c = conn.cursor()
    # Check if creator exists
    c.execute(
        "SELECT creatorID FROM creators WHERE firstName=? AND lastName=?",
        (first, last),
    )
    row = c.fetchone()
    if row:
        creator_id = row[0]
    else:
        c.execute(
            "INSERT INTO creators (firstName, lastName) VALUES (?, ?)",
            (first, last),
        )
        creator_id = c.lastrowid

    c.execute(
        "INSERT INTO itemCreators (itemID, creatorID, creatorTypeID, orderIndex) VALUES (?, ?, ?, ?)",
        (item_id, creator_id, creator_type, order_index),
    )


def _storage_dir() -> Path:
    """Return Zotero's storage directory for the active profile."""
    profile_dir = ZOTERO_DB.parent  # ~/Zotero/
    # Zotero 7 storage is in the profile directory
    import glob as _glob
    profiles = _glob.glob(str(profile_dir / "Profiles" / "*"))
    if profiles:
        return Path(profiles[0]) / "storage"
    # Fallback: Zotero 6 style
    storage = profile_dir / "storage"
    if storage.exists():
        return storage
    raise FileNotFoundError("Cannot find Zotero storage directory")


def add_paper(
    conn: sqlite3.Connection,
    *,
    title: str,
    authors: list[str] | None = None,
    abstract: str = "",
    year: int | None = None,
    venue: str = "",
    doi: str = "",
    url: str = "",
    pages: str = "",
    volume: str = "",
    issue: str = "",
    pdf_path: str | None = None,
    item_type: int = ITEM_TYPE_JOURNAL,
    library_id: int = 1,
) -> int:
    """Insert a paper into Zotero, optionally attaching a PDF. Returns itemID."""
    c = conn.cursor()
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    zkey = _zotero_key()

    c.execute(
        """INSERT INTO items (itemTypeID, key, libraryID, dateAdded, dateModified,
           clientDateModified, version)
           VALUES (?, ?, ?, ?, ?, ?, 0)""",
        (item_type, zkey, library_id, now, now, now),
    )
    item_id = c.lastrowid

    # Core fields
    _set_field(conn, item_id, F_TITLE, title)
    _set_field(conn, item_id, F_ABSTRACT, abstract)
    _set_field(conn, item_id, F_DATE, str(year) if year else "")
    _set_field(conn, item_id, F_PUBLICATION, venue)
    _set_field(conn, item_id, F_DOI, doi)
    _set_field(conn, item_id, F_URL, url)
    _set_field(conn, item_id, F_PAGES, pages)
    _set_field(conn, item_id, F_VOLUME, volume)
    _set_field(conn, item_id, F_ISSUE, issue)
    _set_field(conn, item_id, F_ACCESS_DATE, now[:10])

    # Authors
    if authors:
        for i, author in enumerate(authors):
            _add_creator(conn, item_id, author, i)

    # ── PDF Attachment ──
    if pdf_path:
        pdf_file = Path(pdf_path)
        if pdf_file.exists():
            pdf_key = _zotero_key()
            # Create attachment item
            c.execute(
                """INSERT INTO items (itemTypeID, key, libraryID, dateAdded, dateModified,
                   clientDateModified, version)
                   VALUES (?, ?, ?, ?, ?, ?, 0)""",
                (3, pdf_key, library_id, now, now, now),
            )
            attach_id = c.lastrowid

            # Link to parent
            safe_name = pdf_file.name
            c.execute(
                """INSERT INTO itemAttachments
                   (itemID, parentItemID, linkMode, contentType, path, syncState)
                   VALUES (?, ?, 0, 'application/pdf', ?, 0)""",
                (attach_id, item_id, f"storage:{safe_name}"),
            )

            # Set filename and title on attachment
            _set_field(conn, attach_id, 1, safe_name)  # title = filename

            # Copy PDF to Zotero storage
            storage = _storage_dir() / pdf_key
            storage.mkdir(parents=True, exist_ok=True)
            dest = storage / safe_name
            if not dest.exists():
                import shutil
                shutil.copy2(pdf_file, dest)

    return item_id


def add_to_collection(conn: sqlite3.Connection, item_id: int, collection_id: int) -> None:
    """Add an item to a collection."""
    c = conn.cursor()
    # Get next order index
    c.execute(
        "SELECT MAX(orderIndex) FROM collectionItems WHERE collectionID=?",
        (collection_id,),
    )
    row = c.fetchone()
    next_order = (row[0] or 0) + 1
    c.execute(
        "INSERT INTO collectionItems (collectionID, itemID, orderIndex) VALUES (?, ?, ?)",
        (collection_id, item_id, next_order),
    )


def find_or_create_collection(
    conn: sqlite3.Connection, name: str, library_id: int = 1
) -> int:
    """Find a collection by name, or create it. Returns collectionID."""
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


# ── Better BibTeX CAYW (no-close) path ────────────────────────────────

BBT_CAYW_URL = "http://127.0.0.1:23119/better-bibtex/cayw"


def _paper_to_bibtex(paper: dict[str, Any], cite_key: str) -> str:
    """Convert a paper dict to a BibTeX entry string."""
    authors = paper.get("authors", [])
    author_str = " and ".join(authors) if authors else "Unknown"

    entry_type = "article"
    title = paper.get("title", "")
    year = paper.get("year", "")
    venue = paper.get("venue", "")
    doi = paper.get("doi", "")
    url = paper.get("url", "")
    abstract = paper.get("abstract", "")

    lines = [f"@{entry_type}{{{cite_key},"]
    lines.append(f"  title = {{{title}}},")
    lines.append(f"  author = {{{author_str}}},")
    if year:
        lines.append(f"  year = {{{year}}},")
    if venue:
        lines.append(f"  journal = {{{venue}}},")
    if doi:
        lines.append(f"  doi = {{{doi}}},")
    if url:
        lines.append(f"  url = {{{url}}},")
    if abstract:
        # Truncate abstract to avoid overly long BibTeX fields
        short_abstract = abstract[:500]
        lines.append(f"  abstract = {{{short_abstract}}},")
    lines.append("}")

    return "\n".join(lines)


def _cayw_import(bibtex: str) -> bool:
    """Import a BibTeX entry via Better BibTeX CAYW. Returns True on success."""
    import urllib.request
    import urllib.error

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
        # 400 often means duplicate or minor format issue — log and continue
        print(f"    CAYW HTTP {e.code}: {body[:120]}")
        return False
    except OSError:
        return False


def _cayw_available() -> bool:
    """Check if Better BibTeX CAYW endpoint is reachable (Zotero running)."""
    import urllib.request
    import urllib.error

    try:
        req = urllib.request.Request(BBT_CAYW_URL, method="HEAD")
        with urllib.request.urlopen(req, timeout=2):
            return True
    except urllib.error.HTTPError:
        # HEAD not allowed, but endpoint exists — try POST with minimal BibTeX
        try:
            minimal = "@article{_test,title={_test},author={Test}}"
            req = urllib.request.Request(
                f"{BBT_CAYW_URL}?progid=lit-review",
                data=minimal.encode("utf-8"),
                headers={"Content-Type": "text/plain"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except urllib.error.HTTPError:
            # Endpoint exists but rejected our test — that means it's available
            return True
        except OSError:
            return False
    except OSError:
        return False


def _sqlite_available() -> bool:
    """Check if Zotero SQLite is writable (Zotero closed)."""
    import sqlite3
    try:
        conn = sqlite3.connect(str(ZOTERO_DB))
        conn.execute("SELECT 1 FROM items LIMIT 1")
        conn.close()
        return True
    except sqlite3.OperationalError:
        return False


def sync_papers(
    papers: list[dict[str, Any]],
    collection: str = "Enginnering",
    db_path: Path | None = None,
) -> int:
    """Sync papers into Zotero. Auto-selects CAYW (no-close) or SQLite (close).

    Args:
        papers: List of dicts with keys: title, authors, abstract, year, venue, doi, url
        collection: Target collection name
        db_path: Path to zotero.sqlite (default: ~/Zotero/zotero.sqlite)

    Returns:
        Number of papers inserted
    """
    # Try CAYW first (Zotero running, no close needed)
    if _cayw_available():
        print("Using Better BibTeX CAYW (Zotero running, no close needed)\n")
        count = 0
        for i, p in enumerate(papers):
            cite_key = f"CHP-{p.get('year', '?')}-{i+1:02d}"
            bibtex = _paper_to_bibtex(p, cite_key)
            if _cayw_import(bibtex):
                print(f"  ✓ {p.get('title', '?')[:80]}")
                count += 1
            else:
                print(f"  ✗ {p.get('title', '?')[:80]}")
        print(f"\nNote: items imported to Zotero inbox. Drag to '{collection}' collection.")
        return count

    # Fall back to SQLite (Zotero must be closed)
    db = Path(db_path) if db_path else ZOTERO_DB
    if not db.exists():
        raise FileNotFoundError(f"Zotero database not found: {db}")
    if not _sqlite_available():
        raise RuntimeError(
            "Zotero is running and Better BibTeX CAYW is not available.\n"
            "Options:\n"
            "  1. Install Better BibTeX for Zotero (recommended)\n"
            "  2. Close Zotero and retry (uses SQLite sync)"
        )

    print("Using SQLite sync (Zotero is closed)\n")
    conn = sqlite3.connect(str(db))
    try:
        coll_id = find_or_create_collection(conn, collection)
        count = 0
        for p in papers:
            item_id = add_paper(
                conn,
                title=p.get("title", ""),
                authors=p.get("authors", []),
                abstract=p.get("abstract", ""),
                year=p.get("year"),
                venue=p.get("venue", ""),
                doi=p.get("doi", ""),
                url=p.get("url", ""),
            )
            add_to_collection(conn, item_id, coll_id)
            count += 1
            print(f"  ✓ {p.get('title', '?')[:80]}")
    finally:
        conn.commit()
        conn.close()
    return count
