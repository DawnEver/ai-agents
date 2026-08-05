# -*- coding: utf-8 -*-
"""markdown → docx patch-back renderer.

Reads a `docx2md.py` transcript (.md), walks the ORIGINAL template .docx
(which still carries the `ccxN` bookmarks), and patches each anchored block
with the md's content. Original layout and styles survive; unanchored
(new) blocks are inserted after the previous anchored block.

Usage:  python scripts/md2docx.py <input.md> <template.docx> [output.docx]
"""
import copy
import io
import os
import re
import sys
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT

ANCHOR_PREFIX = "ccx"
ANCHOR_ONLY = re.compile(r"^<!--\s*(ccx\d+)\s*-->$")
HEADING_LINE = re.compile(r"^(#{1,6})\s*(?:<!--\s*(ccx\d+)\s*-->)?\s*(.*)$")
LIST_LINE = re.compile(r"^\s*(?:[-*]|\d+\.)\s+(?:<!--\s*(ccx\d+)\s*-->)?\s*(.*)$")
HEADER_LINE = re.compile(
    r"^>\s*\*\*(HEADER|FOOTER)\*\*\s*(?:<!--\s*(ccx\d+)\s*-->)?\s*(.*)$")

# ------------------------------------------------------------ inline markdown

TOKEN_RE = re.compile(
    r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]*\]\([^)]*\)|[^*`]+)")

def parse_inline(text):
    """→ [(text, fmt)] with fmt in '', 'b', 'i', 'code', or ('link', url)."""
    tokens = []
    for m in TOKEN_RE.finditer(text):
        tok = m.group(0)
        if tok.startswith("**") and tok.endswith("**") and len(tok) > 4:
            tokens.append((tok[2:-2], "b"))
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2:
            tokens.append((tok[1:-1], "i"))
        elif tok.startswith("`") and tok.endswith("`"):
            tokens.append((tok[1:-1], "code"))
        else:
            link = re.match(r"\[([^\]]*)\]\(([^)]*)\)", tok)
            if link and link.group(0) == tok:
                tokens.append((link.group(1), ("link", link.group(2))))
            else:
                tokens.append((tok, ""))
    return tokens


def _make_element(elm, tag, attrs=None):
    e = elm.makeelement(qn(tag), attrs or {})
    return e


def _new_run(paragraph, text, fmt, link_part):
    elm = paragraph._p
    if isinstance(fmt, tuple) and fmt[0] == "link":
        url = fmt[1]
        rel = link_part.relate_to(url, RT.HYPERLINK, is_external=True)
        link = _make_element(elm, "w:hyperlink", {qn("r:id"): rel.rId})
        run = _make_element(elm, "w:r")
        link.append(run)
        elm.append(link)
    else:
        run = _make_element(elm, "w:r")
        elm.append(run)
    if fmt in ("b", "i", "code"):
        rpr = _make_element(elm, "w:rPr")
        if fmt == "b":
            rpr.append(_make_element(elm, "w:b"))
        elif fmt == "i":
            rpr.append(_make_element(elm, "w:i"))
        else:
            rpr.append(_make_element(elm, "w:rFonts", {
                qn("w:ascii"): "Consolas", qn("w:hAnsi"): "Consolas"}))
        run.append(rpr)
    t = _make_element(elm, "w:t")
    t.text = text
    run.append(t)


def set_paragraph_md(p, text, link_part):
    """Replace a paragraph's runs with parsed inline markdown.
    Keeps w:pPr and any ccx bookmark pair (the round-trip anchors)."""
    elm = p._p
    for child in list(elm):
        if child.tag in (qn("w:pPr"), qn("w:bookmarkStart"),
                         qn("w:bookmarkEnd")):
            continue
        elm.remove(child)
    for text_i, fmt in parse_inline(text):
        _new_run(p, text_i, fmt, link_part)


def set_cell_text(cell, text, link_part):
    paras = cell.paragraphs
    for extra in paras[1:]:
        extra._p.getparent().remove(extra._p)
    set_paragraph_md(paras[0], text, link_part)


# -------------------------------------------------------------- md parsing

def _parse_table(lines):
    rows = []
    for line in lines:
        cells = [c.strip().replace(r"\|", "|") for c in line.strip().strip("|").split("|")]
        # separator row = every cell is dashes; empty cells are DATA, not separators
        if cells and all(c and re.fullmatch(r":?-{3,}:?", c) for c in cells):
            continue
        rows.append(cells)
    return rows


PARA_ANCHOR = re.compile(r"^<!--\s*(ccx\d+)\s*-->\s*(.*)$")
PLAIN_COMMENT = re.compile(r"^<!--.*-->$")


def _parse_md_full(text):
    """→ list of block dicts:
    {kind: 'empty'|'para'|'heading'|'list'|'header'|'table',
     anchor: id|None, text?, level?, rows?}
    Tables are consumed contiguously (index-based loop)."""
    lines = text.splitlines()
    blocks = []
    pending = None
    i = 0
    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()
        m = ANCHOR_ONLY.match(line)
        if m:
            pending = m.group(1)
            i += 1
            continue
        if not line.strip():
            if pending:
                blocks.append({"kind": "empty", "anchor": pending})
                pending = None
            i += 1
            continue
        if line.lstrip().startswith("|"):
            tbl = [line]
            i += 1
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                tbl.append(lines[i].rstrip())
                i += 1
            blocks.append({"kind": "table", "anchor": pending,
                           "rows": _parse_table(tbl)})
            pending = None
            continue
        m = HEADER_LINE.match(line)
        if m:
            blocks.append({"kind": "header", "anchor": m.group(2),
                           "text": m.group(3)})
            i += 1
            continue
        m = HEADING_LINE.match(line)
        if m:
            blocks.append({"kind": "heading", "anchor": m.group(2),
                           "level": len(m.group(1)), "text": m.group(3)})
            i += 1
            continue
        m = LIST_LINE.match(line)
        if m:
            blocks.append({"kind": "list", "anchor": m.group(1),
                           "text": m.group(2)})
            i += 1
            continue
        m = PARA_ANCHOR.match(line)  # extraction format: <!-- ccxN --> text
        if m:
            blocks.append({"kind": "para", "anchor": m.group(1),
                           "text": m.group(2)})
            i += 1
            continue
        if PLAIN_COMMENT.match(line):
            i += 1  # metadata comment (e.g. transcript header) — skip
            continue
        blocks.append({"kind": "para", "anchor": pending, "text": line})
        pending = None
        i += 1
    if pending:
        blocks.append({"kind": "empty", "anchor": pending})
    return blocks


# ---------------------------------------------------------------- anchors

def _block_anchors(root, anchors):
    """Find ccxN bookmarkStart elements under `root`; record target block."""
    for bm in root.iter(qn("w:bookmarkStart")):
        name = bm.get(qn("w:name") or "")
        if not name.startswith(ANCHOR_PREFIX):
            continue
        parent = bm.getparent()
        if parent.tag == qn("w:p"):
            anchors[name] = ("p", parent)
        else:
            nxt = bm.getnext()
            if nxt is not None and nxt.tag in (qn("w:p"), qn("w:tbl")):
                anchors[name] = (nxt.tag.rsplit("}", 1)[-1], nxt)


def build_anchor_map(doc):
    anchors = {}
    _block_anchors(doc.element.body, anchors)
    for section in doc.sections:
        for container in (section.header, section.footer):
            _block_anchors(container._element, anchors)
    return anchors


# ------------------------------------------------------------- table sync

def sync_table(table, md_rows, link_part):
    """Fill table from md rows. Grid-indexed: row.cells maps 1:1 to md cells
    (merged cells are written at every spanned position — same tc, same text)."""
    nrows = len(md_rows)
    while len(table.rows) < nrows:
        last = table.rows[-1]._tr
        last.addnext(copy.deepcopy(last))
    while len(table.rows) > nrows:
        tr = table.rows[-1]._tr
        tr.getparent().remove(tr)
    for r in range(nrows):
        cells = table.rows[r].cells
        for c in range(min(len(cells), len(md_rows[r]))):
            set_cell_text(cells[c], md_rows[r][c], link_part)


# --------------------------------------------------------------- insert

def insert_block(doc, body_elm, cursor, block, link_part):
    """Insert an unanchored block after cursor; returns the new element."""
    if block["kind"] == "table":
        t = doc.add_table(rows=len(block["rows"]),
                          cols=max((len(r) for r in block["rows"]), default=1))
        if "Table Grid" in [s.name for s in doc.styles]:
            t.style = doc.styles["Table Grid"]
        tbl = t._tbl
        body_elm.remove(tbl)
        cursor.addnext(tbl)
        sync_table(t, block["rows"], link_part)
        return tbl
    # paragraph-like
    if block["kind"] == "heading":
        style = f"Heading {block.get('level', 1)}"
    else:
        style = None
    p = doc.add_paragraph("", style=style) if style else doc.add_paragraph()
    body_elm.remove(p._p)
    cursor.addnext(p._p)
    set_paragraph_md(p, block.get("text", ""), link_part)
    return p._p


# ----------------------------------------------------------------- main

def md2docx(md_path, docx_path, out_path):
    with io.open(md_path, encoding="utf-8") as f:
        md_text = f.read()
    doc = Document(docx_path)
    body_elm = doc.element.body
    anchors = build_anchor_map(doc)
    link_part = doc.part

    cursor = None
    for block in _parse_md_full(md_text):
        if block["anchor"]:
            entry = anchors.get(block["anchor"])
            if entry is None:  # unmatched anchor → leave original untouched
                continue
            kind, elm = entry
            if kind == "p" and block["kind"] != "table":
                p = Paragraph(elm, doc)
                set_paragraph_md(p, block.get("text", ""), link_part)
            elif kind == "tbl" and block["kind"] == "table":
                sync_table(Table(elm, doc), block["rows"], link_part)
            else:
                continue  # kind mismatch → skip silently
            if elm.getparent() is body_elm:  # only body blocks position inserts
                cursor = elm
        else:
            if cursor is None:
                cursor = body_elm[0]
            cursor = insert_block(doc, body_elm, cursor, block, link_part)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    doc.save(out_path)
    print(f"rendered: {out_path}")


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    md_path, docx_path = sys.argv[1], sys.argv[2]
    if len(sys.argv) > 3:
        out_path = sys.argv[3]
    else:
        stem = os.path.splitext(os.path.basename(docx_path))[0]
        out_path = os.path.join("out", stem + "-filled.docx")
    md2docx(md_path, docx_path, out_path)


if __name__ == "__main__":
    main()
