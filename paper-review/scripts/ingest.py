#!/usr/bin/env python3
"""
Ingest a PDF into per-section markdown + images.

Tool selection:
  - GPU with ≥4 GB VRAM → marker-pdf  (best quality)
  - otherwise           → pymupdf4llm (fast, rule-based)
  - fallback            → pdfplumber   (plain text only)

Multi-paper handling:
  - Detects appended conference papers / prior versions after the main paper.
  - Saves them to <out-dir>/appended/<N>-<title-slug>/ with their own paper.md + md/.

Usage:
  python scripts/ingest.py <pdf-path> <out-dir>
"""

import re
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Optional


# ── GPU detection ────────────────────────────────────────────────────────────

def _detect_gpu_vram_gb() -> float:
    """Return available VRAM in GB, or 0 if no usable GPU found."""
    # Metal (Apple Silicon) — check for "Chipset Model" first
    try:
        out = subprocess.check_output(
            ["system_profiler", "SPDisplaysDataType"], text=True, timeout=5
        )
        for line in out.splitlines():
            # Apple Silicon: unified memory, listed as "Chipset Model: Apple M4"
            # Use total system memory as a proxy
            if 'Chipset Model: Apple' in line:
                # Apple Silicon — check total RAM via sysctl
                try:
                    ram = subprocess.check_output(
                        ["sysctl", "-n", "hw.memsize"], text=True, timeout=3
                    )
                    total_gb = int(ram.strip()) / 1e9
                except Exception:
                    total_gb = 8.0  # reasonable default for Apple Silicon
                return total_gb * 0.7  # conservative: 70% of RAM usable
            m = re.search(r"VRAM.*?(\d+)\s*(GB|MB)", line, re.IGNORECASE)
            if m:
                v = float(m.group(1))
                return v if m.group(2).upper() == "GB" else v / 1024
    except Exception:
        pass

    # CUDA
    try:
        import torch
        if torch.cuda.is_available():
            return torch.cuda.get_device_properties(0).total_memory / 1e9
    except Exception:
        pass

    # nvidia-smi
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            text=True, timeout=5,
        )
        mb = float(out.strip().splitlines()[0])
        return mb / 1024
    except Exception:
        pass

    return 0.0


def _choose_tool() -> str:
    vram = _detect_gpu_vram_gb()
    print(f"[ingest] detected VRAM: {vram:.1f} GB", file=sys.stderr)
    if vram >= 4:
        return "marker"
    return "pymupdf4llm"


# ── Converters ───────────────────────────────────────────────────────────────

def _run_marker(pdf: Path, out_dir: Path) -> str:
    """Run marker_single; return markdown text."""
    tmp = out_dir / "_marker_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            ["marker_single", str(pdf), "--output_format", "markdown", "--output_dir", str(tmp)],
            check=True,
        )
        # marker writes <stem>/<stem>.md
        md_files = list(tmp.rglob("*.md"))
        if not md_files:
            raise RuntimeError("marker produced no markdown")
        text = md_files[0].read_text()
        # copy images
        for img in list(tmp.rglob("*.png")) + list(tmp.rglob("*.jpeg")) + list(tmp.rglob("*.jpg")):
            dest = out_dir / "img" / "flat" / img.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(img, dest)
        return text
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _run_pymupdf4llm(pdf: Path, out_dir: Path) -> str:
    import pymupdf4llm
    (out_dir / "img" / "flat").mkdir(parents=True, exist_ok=True)
    md = pymupdf4llm.to_markdown(str(pdf), write_images=True, image_path=str(out_dir / "img" / "flat"))
    return md


def _run_pdfplumber(pdf: Path, out_dir: Path) -> str:
    import pdfplumber
    parts = []
    with pdfplumber.open(str(pdf)) as p:
        for i, page in enumerate(p.pages, 1):
            text = page.extract_text() or ""
            parts.append(f"<!-- page {i} -->\n{text}")
    return "\n\n".join(parts)


def _convert(pdf: Path, out_dir: Path) -> tuple[str, str]:
    """Return (markdown_text, tool_used)."""
    tool = _choose_tool()
    print(f"[ingest] trying {tool}", file=sys.stderr)
    try:
        if tool == "marker":
            return _run_marker(pdf, out_dir), "marker"
        elif tool == "pymupdf4llm":
            return _run_pymupdf4llm(pdf, out_dir), "pymupdf4llm"
        else:
            raise ValueError(f"Unknown tool: {tool}")
    except Exception as e:
        print(f"[ingest] {tool} failed ({e}), falling back to pdfplumber", file=sys.stderr)
        return _run_pdfplumber(pdf, out_dir), "pdfplumber"


# ── Section splitter ─────────────────────────────────────────────────────────

def _split_sections(md: str) -> list[tuple[str, str]]:
    """
    Split markdown into (heading, body) pairs. heading='' for preamble.

    Picks the *shallowest* heading level that has ≥3 matches (favours
    top-level sections over fine-grained subsections).  Falls back to
    all-heading split when no single level reaches the threshold.
    """
    # count headings at levels 1-3
    counts = {lvl: len(re.findall(rf"^{'#'*lvl} ", md, re.MULTILINE)) for lvl in (1, 2, 3)}

    # pick shallowest level with ≥3 matches
    best = None
    for lvl in (1, 2, 3):
        if counts[lvl] >= 3:
            best = lvl
            break

    if best is not None:
        # Single-level split: inner capture "(##)" → 2 groups per heading
        pattern = rf"^({'#'*best})\s"
        parts = re.split(f"({pattern}.*)", md, flags=re.MULTILINE)
        sections: list[tuple[str, str]] = []
        preamble = parts[0].strip()
        if preamble:
            sections.append(("", preamble))
        i = 1
        while i < len(parts) - 2:
            heading_line = parts[i].strip()  # full heading line
            body = parts[i + 2].strip()      # skip inner capture group at i+1
            sections.append((heading_line, body))
            i += 3
    else:
        # All-heading fallback: single capture group → 1 group per heading
        pattern = r"^#+\s"
        parts = re.split(f"({pattern}.*)", md, flags=re.MULTILINE)
        sections = []
        preamble = parts[0].strip()
        if preamble:
            sections.append(("", preamble))
        i = 1
        while i < len(parts) - 1:
            heading_line = parts[i].strip()
            body = parts[i + 1].strip() if i + 1 < len(parts) else ""
            sections.append((heading_line, body))
            i += 2

    if len(sections) < 2:
        return [("", md)]

    return sections


# ── Post-processing ──────────────────────────────────────────────────────────

def _strip_formatting(text: str) -> str:
    """Remove markdown images, links, and formatting characters."""
    clean = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    clean = re.sub(r'\[([^\]]*)\]\(.*?\)', r'\1', clean)
    clean = re.sub(r'[*#>|_\-`\s]', '', clean)
    return clean


def _classify_section(heading: str, body: str) -> str:
    """
    Classify a section as 'keep', 'discard', or 'merge-up'.

    'merge-up': heading is a diagram label (e.g. (a), (b)) — discard
    the heading but merge its body into the previous section.
    'discard':  pure OCR noise — discard heading and body.
    'keep':     legitimate section.
    """
    clean_body = _strip_formatting(body)
    clean_heading = re.sub(r'[*#]', '', heading).strip()

    # diagram sub-labels: (a), (b), (c), (d) — never real sections
    if re.match(r'^\([a-z]\)$', clean_heading):
        return 'merge-up'

    # body too short to be substantive → discard
    if len(clean_body) < 80:
        return 'discard'

    # diagram-label headings from figure/diagram fragments
    #   **Flux**, **V abc**, **I sd [*]**, **V abc [*]**
    if re.match(
        r'^\*{0,2}[A-Za-z_][\w\s\[\]*]{0,20}\*{0,2}$',
        clean_heading,
    ):
        # body is mostly garbled table markup → discard
        if len(clean_body) < 400:
            pipe_ratio = clean_body.count('|') / max(len(clean_body), 1)
            if pipe_ratio > 0.05:
                return 'discard'
        # or body is short enough to be just figure caption remnants
        if len(clean_body) < 200:
            return 'discard'

    return 'keep'


def _is_paper_boundary(heading: str, body: str, idx: int) -> bool:
    """
    Detect if this section starts a new independent paper appended after
    the main paper.  Only checked for sections beyond the first few.
    """
    if idx < 5:
        return False

    combined = heading + "\n" + body[:3000]

    # Author block signals (affiliations + emails)
    author_score = 0
    if re.search(r'@\w+\.\w+\.?\w+', combined):
        author_score += 1
    if re.search(r'(?:University|Institute|College|Technische)\s+(?:of\s+)?\w+', combined):
        author_score += 1
    if re.search(r'\b(?:Student\s+Member|Fellow|Senior\s+Member|Member)\s*,?\s*IEEE\b', combined):
        author_score += 1
    if re.search(r'\{[^}]*@[^}]*\}', combined):   # LaTeX email
        author_score += 1
    if author_score >= 2:
        return True

    # IEEE copyright banner (appears on first page of IEEE papers)
    if re.search(r'©\s*20\d{2}\s*IEEE', combined):
        return True

    # "Authorized licensed use limited to" — IEEE Xplore stamp
    if 'Authorized licensed use limited to' in combined and idx >= 5:
        return True

    # IEEE conference header line
    if re.search(r'20\d{2}\s+IEEE\s+.*?(?:Conference|Expo|Convention)', combined):
        return True

    # Roman-numeral section restart (I. INTRODUCTION) after Arabic sections
    if re.search(r'\bI\.\s+INTRODUCTION\b', combined) and idx >= 5:
        return True

    # IEEE-style abstract after references section
    if idx >= 5 and re.search(r'Abstract[—\-]', combined):
        return True

    return False


def _paper_title_from_sections(sections: list[tuple[str, str]]) -> str:
    """Extract a title from the first heading of a paper fragment."""
    for heading, _body in sections:
        if heading:
            return heading.lstrip('#').strip()[:80]
    return "untitled"


def _clean_sections(
    sections: list[tuple[str, str]]
) -> tuple[list[tuple[str, str]], list[tuple[str, list[tuple[str, str]]]]]:
    """
    Filter noise sections and detect appended-paper boundaries.

    Returns:
      main_sections  — sections belonging to the primary paper
      appended       — list of (title, sections) for each appended paper
    """
    # first pass: classify and merge/discard
    cleaned: list[tuple[str, str]] = []
    for heading, body in sections:
        action = _classify_section(heading, body)
        if action == 'discard':
            continue
        elif action == 'merge-up':
            if cleaned:
                prev_heading, prev_body = cleaned[-1]
                cleaned[-1] = (prev_heading, prev_body + '\n\n' + body)
            elif heading:
                cleaned.append((heading, body))
        else:
            cleaned.append((heading, body))

    # second pass: find paper boundaries
    main_sections: list[tuple[str, str]] = []
    appended: list[tuple[str, list[tuple[str, str]]]] = []
    current_batch: list[tuple[str, str]] = []
    found_boundary = False

    for idx, (heading, body) in enumerate(cleaned):
        if _is_paper_boundary(heading, body, idx):
            if current_batch:
                if not found_boundary:
                    main_sections = current_batch
                    found_boundary = True
                else:
                    title = _paper_title_from_sections(current_batch)
                    appended.append((title, current_batch))
            current_batch = [(heading, body)]
        else:
            current_batch.append((heading, body))

    # final batch
    if current_batch:
        if not found_boundary:
            main_sections = current_batch
        else:
            title = _paper_title_from_sections(current_batch)
            appended.append((title, current_batch))

    return main_sections, appended


# ── Figure page rendering ────────────────────────────────────────────────────

def _build_figure_page_map(pdf_path: Path) -> dict[str, int]:
    """
    Return dict mapping normalized figure/table labels to 0-based page numbers.

    NOTE: Records the *first* page on which a figure label is mentioned in
    the PDF text layer.  This is typically the callout/reference page, not
    necessarily the display page where the figure actually appears.  The
    rendered page image will still contain the full page including any
    surrounding text, so downstream reviewers can assess the context.
    """
    import fitz
    figure_pages: dict[str, int] = {}
    doc = fitz.open(str(pdf_path))
    for page_num in range(len(doc)):
        text = doc[page_num].get_text()
        for m in re.finditer(r'(Figure\s+\d+|Fig\.\s*\d+|Table\s+\d+)', text, re.IGNORECASE):
            label = m.group(1)
            normalized = re.sub(r'^Fig\.\s*', 'Figure ', label)
            if normalized not in figure_pages:
                figure_pages[normalized] = page_num
    doc.close()
    return figure_pages


def _render_figure_pages(
    pdf_path: Path,
    out_dir: Path,
    body_sections: list[tuple[str, str]],
) -> dict[str, str]:
    """
    Render PDF pages containing figures as full-page images.

    Returns mapping from figure label → relative image path (for INDEX.md).
    Pages are rendered at ~144 DPI — readable axis labels without huge files.
    """
    import fitz
    figure_page_map = _build_figure_page_map(pdf_path)
    figure_images: dict[str, str] = {}
    rendered_pages: set[int] = set()
    _page_filename: dict[int, str] = {}  # actual on-disk filename per page

    doc = fitz.open(str(pdf_path))

    for idx, (heading, _) in enumerate(body_sections, 1):
        slug = _slug(heading) or "body"
        sec_file = out_dir / "md" / f"{idx:02d}-{slug}.md"
        if not sec_file.exists():
            continue
        content = sec_file.read_text()
        sec_img_dir = out_dir / "img" / f"sec{idx:02d}"
        sec_img_dir.mkdir(parents=True, exist_ok=True)

        for m in re.finditer(r'(Figure\s+\d+|Fig\.\s*\d+|Table\s+\d+)', content, re.IGNORECASE):
            label = m.group(1)
            normalized = re.sub(r'^Fig\.\s*', 'Figure ', label)
            page_num = figure_page_map.get(normalized)
            if page_num is None:
                continue

            img_name = f"page-{page_num+1:02d}-{normalized.lower().replace(' ', '-')}.png"
            if page_num not in rendered_pages:
                page = doc[page_num]
                mat = fitz.Matrix(2.0, 2.0)  # ~144 DPI
                pix = page.get_pixmap(matrix=mat)
                img_path = sec_img_dir / img_name
                pix.pil_save(str(img_path))
                rendered_pages.add(page_num)
                _page_filename[page_num] = img_name

            # use the actual rendered filename, not one derived from the current match
            actual_name = _page_filename.get(page_num, img_name)
            if normalized not in figure_images:
                figure_images[normalized] = f"img/sec{idx:02d}/{actual_name}"

    doc.close()
    return figure_images


# ── Output helpers ──────────────────────────────────────────────────────────

def _slug(text: str, maxlen: int = 30) -> str:
    s = re.sub(r"^#+\s*", "", text).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:maxlen].strip("-")


def _write_section_files(
    body_sections: list[tuple[str, str]], md_dir: Path
) -> list[dict]:
    """Write per-section markdown files. Returns section info list (idx, heading, slug, fname)."""
    if md_dir.exists():
        for old in md_dir.iterdir():
            old.unlink()
    md_dir.mkdir(parents=True, exist_ok=True)

    section_info = []
    for idx_s, (heading, body) in enumerate(body_sections, 1):
        slug = _slug(heading) or "body"
        fname = f"{idx_s:02d}-{slug}.md"
        (md_dir / fname).write_text(f"{heading}\n\n{body}\n")
        section_info.append({"idx": idx_s, "heading": heading, "slug": slug, "fname": fname})
    return section_info


def _route_images(
    img_flat: Path,
    body_sections: list[tuple[str, str]],
    md_dir: Path,
    images_dir: Path,
) -> None:
    """Distribute flat images to per-section directories and rewrite image references."""
    # Cache section file contents once to avoid O(n*m) re-reads
    section_contents: dict[int, str] = {}
    for idx_s, (heading, _) in enumerate(body_sections, 1):
        slug = _slug(heading) or "body"
        sec_file = md_dir / f"{idx_s:02d}-{slug}.md"
        if sec_file.exists():
            section_contents[idx_s] = sec_file.read_text()

    for img_file in img_flat.iterdir():
        if not img_file.is_file():
            continue
        referenced_in = None
        for idx_s, content in section_contents.items():
            # Use word-boundary regex to avoid substring false positives
            if re.search(rf'\b{re.escape(img_file.name)}\b', content):
                referenced_in = idx_s
                break
        dest_folder = (
            images_dir / f"sec{referenced_in:02d}" if referenced_in
            else images_dir / "orphan"
        )
        dest_folder.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(img_file), dest_folder / img_file.name)

    # Rewrite image refs in section files to relative paths
    for idx_s in section_contents:
        sec_file = md_dir / f"{idx_s:02d}-{_slug(body_sections[idx_s - 1][0]) or 'body'}.md"
        content = section_contents[idx_s]
        content = re.sub(
            r"!\[([^\]]*)\]\((?:.*img/flat/)?([^)\s]+)[^)]*\)",
            lambda m: f"![{m.group(1)}](../img/sec{idx_s:02d}/{m.group(2)})",
            content,
        )
        sec_file.write_text(content)


def _build_index(
    out_dir: Path,
    md_dir: Path,
    body_sections: list[tuple[str, str]],
    figure_images: dict[str, str],
) -> tuple[int, int]:
    """Build and write INDEX.md. Returns (n_figures, n_tables)."""
    index_rows = ["| Number | File | Referenced in | Caption |", "|--------|------|---------------|---------|"]
    fig_pattern = re.compile(r"(Figure\s+\d+|Fig\.\s*\d+|Table\s+\d+)", re.IGNORECASE)
    seen: dict[str, str] = {}
    for idx_s, (heading, _) in enumerate(body_sections, 1):
        slug = _slug(heading) or "body"
        sec_file = md_dir / f"{idx_s:02d}-{slug}.md"
        if not sec_file.exists():
            continue
        content = sec_file.read_text()
        for m in fig_pattern.finditer(content):
            label = m.group(1)
            if label not in seen:
                seen[label] = f"md/{idx_s:02d}-{slug}.md"
                if label in figure_images:
                    img_path = figure_images[label]
                else:
                    sec_img_dir = out_dir / "img" / f"sec{idx_s:02d}"
                    imgs = list(sec_img_dir.iterdir()) if sec_img_dir.exists() else []
                    img_path = str(imgs[0].relative_to(out_dir)) if imgs else "—"
                index_rows.append(f"| {label} | {img_path} | md/{idx_s:02d}-{slug}.md | — |")

    (out_dir / "INDEX.md").write_text("# Figure / Table Index\n\n" + "\n".join(index_rows) + "\n")

    n_fig = len([r for r in index_rows if r.startswith("| Figure")])
    n_tbl = len([r for r in index_rows if r.startswith("| Table")])
    return n_fig, n_tbl


def _write_paper_output(
    sections: list[tuple[str, str]],
    out_dir: Path,
    md_text: str,
    title_override=None,
    pdf_path: Optional[Path] = None,
) -> tuple[int, int, int]:
    """
    Write per-section files, paper.md, images, INDEX.md for one paper.
    If pdf_path is given, renders full-page figure images (with axis labels
    and captions) using PyMuPDF.
    Returns (n_sections, n_figures, n_tables).
    """
    md_dir = out_dir / "md"
    img_flat = out_dir / "img" / "flat"
    img_flat.mkdir(parents=True, exist_ok=True)

    body_sections = [s for s in sections if s[0] != ""]
    if not body_sections:
        body_sections = sections

    section_info = _write_section_files(body_sections, md_dir)
    section_links = [
        f"- [{si['idx']:02d} {si['heading'].lstrip('#').strip()}](md/{si['fname']})"
        for si in section_info
    ]

    _route_images(img_flat, body_sections, md_dir, out_dir / "img")

    # extract title: find the earliest level-1/2/3 heading
    if title_override:
        title = title_override
    else:
        title = "Untitled"
        best_pos = None
        for lvl in (1, 2, 3):
            title_m = re.search(rf"^{'#'*lvl}\s+(.+)", md_text, re.MULTILINE)
            if title_m:
                candidate = title_m.group(1).strip()
                if candidate.lower() in ('abstract',):
                    continue
                if best_pos is None or title_m.start() < best_pos:
                    title = candidate
                    best_pos = title_m.start()

    # extract abstract
    preamble_body = sections[0][1] if sections and sections[0][0] == "" else ""
    abstract_m = re.search(
        r"(?:^#{1,3}\s*abstract\s*\n)(.*?)(?=^#{1,3}\s|\Z)",
        md_text, re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    abstract = abstract_m.group(1).strip() if abstract_m else preamble_body[:800]

    # build paper.md
    paper_md = f"# {title}\n\n## Abstract\n{abstract}\n\n## Sections\n" + "\n".join(section_links) + "\n"
    (out_dir / "paper.md").write_text(paper_md)

    # render figure pages and build INDEX.md
    figure_images: dict[str, str] = {}
    if pdf_path and pdf_path.exists():
        figure_images = _render_figure_pages(pdf_path, out_dir, body_sections)

    n_fig, n_tbl = _build_index(out_dir, md_dir, body_sections, figure_images)

    n_sec = len(body_sections)
    return n_sec, n_fig, n_tbl


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) != 3:
        print("Usage: ingest.py <pdf> <out-dir>")
        sys.exit(1)

    pdf = Path(sys.argv[1]).resolve()
    slug_dir = Path(sys.argv[2]).resolve()
    out_dir = slug_dir / "1-paper-text"

    # copy PDF as 0-raw.pdf in slug root
    raw_dest = slug_dir / "0-raw.pdf"
    if pdf != raw_dest:
        shutil.copy2(pdf, raw_dest)

    (out_dir / "img" / "flat").mkdir(parents=True, exist_ok=True)

    md_text, tool_used = _convert(pdf, out_dir)

    # split and clean
    raw_sections = _split_sections(md_text)
    main_sections, appended_papers = _clean_sections(raw_sections)

    if not main_sections:
        print("[ingest] ERROR: no sections found after cleaning", file=sys.stderr)
        sys.exit(1)

    # write main paper
    n_sec, n_fig, n_tbl = _write_paper_output(main_sections, out_dir, md_text, pdf_path=pdf)
    print(f"[ingest] tool={tool_used}  sections={n_sec}  figures≈{n_fig}  tables≈{n_tbl}")
    print(f"[ingest] paper.md written → {out_dir / 'paper.md'}")

    # write appended papers (under 1-paper-text/appended/)
    appended_dir = out_dir / "appended"
    if appended_dir.exists():
        shutil.rmtree(appended_dir)
    if appended_papers:
        appended_dir.mkdir(parents=True, exist_ok=True)
        for i, (title, ap_sections) in enumerate(appended_papers, 1):
            ap_slug = _slug(title) or f"paper-{i}"
            ap_dir = appended_dir / f"{i:02d}-{ap_slug}"
            ap_dir.mkdir(parents=True, exist_ok=True)
            ap_img_flat = ap_dir / "img" / "flat"
            ap_img_flat.mkdir(parents=True, exist_ok=True)
            src_flat = out_dir / "img" / "flat"
            if src_flat.exists():
                for img in src_flat.iterdir():
                    if img.is_file():
                        shutil.copy2(img, ap_img_flat / img.name)
            ap_n_sec, ap_n_fig, ap_n_tbl = _write_paper_output(
                ap_sections, ap_dir, ap_sections[0][1] if ap_sections else "", title_override=title,
            )
            print(f"[ingest]   appended #{i}: \"{title}\"  sections={ap_n_sec}  figures≈{ap_n_fig}")
            print(f"[ingest]   → {ap_dir / 'paper.md'}")

    # cleanup
    shutil.rmtree(out_dir / "_marker_tmp", ignore_errors=True)
    shutil.rmtree(out_dir / "img" / "flat", ignore_errors=True)


if __name__ == "__main__":
    main()
