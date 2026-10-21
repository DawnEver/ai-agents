#!/usr/bin/env python3
"""Render every slide to PNG plus one contact sheet, so the agent (and you) can see the deck.

Usage:
    python scripts/preview_slides.py <deck.pptx> [out_dir] [--dpi 80] [--columns 3]

PowerPoint exports a PDF (see powerpoint.py), Ghostscript rasterises it. Default out_dir is
<deck dir>/preview/<deck stem>/ → slide-01.png … and contact.png. Read contact.png first,
then individual slides for detail.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

import powerpoint

GS_NAMES = ("gs", "gswin64c", "gswin32c")


def default_preview_dir(deck):
    deck = Path(deck)
    return deck.parent / "preview" / deck.stem


def rasterize(pdf, out_dir, dpi=80):
    gs = next((shutil.which(n) for n in GS_NAMES if shutil.which(n)), None)
    if not gs:
        raise powerpoint.PowerPointError("Ghostscript not found (brew install ghostscript / choco install ghostscript)")
    for old in out_dir.glob("slide-*.png"):
        old.unlink()
    subprocess.run([gs, "-q", "-dNOPAUSE", "-dBATCH", "-dSAFER", "-sDEVICE=png16m", f"-r{dpi}",
                    "-dTextAlphaBits=4", "-dGraphicsAlphaBits=4",
                    "-o", str(out_dir / "slide-%02d.png"), str(pdf)], check=True, timeout=300)
    return sorted(out_dir.glob("slide-*.png"))


def contact_sheet(pages, out, columns=3, thumb_width=480, gap=12):
    thumbs = []
    for p in pages:
        with Image.open(p) as im:
            ratio = thumb_width / im.width
            thumbs.append(im.convert("RGB").resize((thumb_width, round(im.height * ratio))))
    th = max(t.height for t in thumbs)
    rows = -(-len(thumbs) // columns)
    label_h = 22
    sheet = Image.new("RGB", (columns * (thumb_width + gap) + gap, rows * (th + label_h + gap) + gap), "white")
    draw = ImageDraw.Draw(sheet)
    for i, t in enumerate(thumbs):
        x = gap + (i % columns) * (thumb_width + gap)
        y = gap + (i // columns) * (th + label_h + gap)
        draw.text((x, y + 4), f"Slide {i + 1}", fill="black")
        sheet.paste(t, (x, y + label_h))
        draw.rectangle([x - 1, y + label_h - 1, x + t.width, y + label_h + t.height], outline="#999999")
    sheet.save(out)
    return Path(out)


def preview(deck, out_dir=None, dpi=80, columns=3):
    deck = Path(deck)
    out_dir = Path(out_dir) if out_dir else default_preview_dir(deck)
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf = powerpoint.export_pdf(deck, out_dir / f"{deck.stem}.pdf")
    pages = rasterize(pdf, out_dir, dpi)
    if not pages:
        raise powerpoint.PowerPointError("rasterisation produced no pages")
    return pages, contact_sheet(pages, out_dir / "contact.png", columns)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("out_dir", nargs="?")
    ap.add_argument("--dpi", type=int, default=80)
    ap.add_argument("--columns", type=int, default=3)
    args = ap.parse_args(argv)
    try:
        pages, sheet = preview(args.deck, args.out_dir, args.dpi, args.columns)
    except (powerpoint.PowerPointError, subprocess.SubprocessError) as e:
        sys.exit(f"error: {e}")
    print(f"{len(pages)} slide(s) → {sheet.parent}")
    print(sheet)


if __name__ == "__main__":
    main()
