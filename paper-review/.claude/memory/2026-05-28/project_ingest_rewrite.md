---
name: project-ingest-rewrite
description: ingest.py overhauled — section splitting, noise filtering, multi-paper detection, figure rendering, GPU detection
metadata:
  type: project
---

ingest.py was substantially rewritten (2026-05-28) to fix critical bugs and add features.

**Why:** The case-study paper (IET EPA + 2 appended IEEE ITEC papers) exposed multiple ingest failures: (1) Section splitter was completely broken in the any-heading fallback mode because regex capture-group count vs iteration stride mismatched; (2) OCR garbage from control-diagram figure fragments was treated as sections; (3) Three independent papers in one PDF were treated as one document; (4) pymupdf4llm's embedded-raster extraction couldn't capture vector figure axes/captions.

**Changes:**
- `_split_sections`: Fixed capture-group-mismatch bug; prefer shallowest heading level with ≥3 matches (not level with most matches → over-fragmentation)
- `_classify_section`: Three-way classifier — 'keep' (normal), 'discard' (OCR garbage: <80 meaningful chars, diagram labels with high pipe-ratio), 'merge-up' (sub-figure labels like (a)/(b) → body merged into parent)
- `_is_paper_boundary`: Detects appended papers via author-block signals (affiliations+email ≥2), IEEE copyright banners, Roman-numeral section restarts, IEEE Abstract- format
- `_build_figure_page_map` + `_render_figure_pages`: Uses PyMuPDF (fitz) to render full pages containing figures/tables at ~144 DPI — preserves axis labels, captions, complete sub-figures. marker-pdf installed but not used (too slow on M4 without dedicated GPU)
- `_detect_gpu_vram_gb`: Added Apple Silicon detection (Chipset Model → sysctl hw.memsize * 0.7)
- Title extraction: Finds earliest level-1/2/3 heading, skips "Abstract"
- Python 3.9 compat: Optional[X] instead of X | None

**How to apply:** Script auto-detects and auto-cleans. Multi-paper detection output goes to `1-paper-text/appended/`. Figure rendering is a post-processing step after pymupdf4llm conversion.
