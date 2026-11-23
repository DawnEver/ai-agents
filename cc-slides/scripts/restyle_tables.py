#!/usr/bin/env python3
"""Give the tables of an existing deck the deck's own table style, copied from a pattern table.

Usage:
    python scripts/restyle_tables.py <deck.pptx> --pattern-slide 40 --slides 23,24 -o <out.pptx>

The first table on --pattern-slide is the style source (slides_lib.apply_table_style: tblPr +
style id, and per cell role -- header row / first column / body -- tcPr, alignment, font size,
run fill). Every table on --slides is restyled; text, bold and equations are kept. Writes a NEW
file; nothing else in the deck changes.
"""
import argparse
import sys
from pathlib import Path

from pptx import Presentation

import slides_lib as lib


def restyle(deck, pattern_slide, slides, out):
    if Path(out).resolve() == Path(deck).resolve():
        raise ValueError("refusing to write over the input deck; choose another output path")
    prs = Presentation(deck)
    n = len(prs.slides)
    for k in [pattern_slide, *slides]:
        if not 1 <= k <= n:
            raise ValueError(f"slide {k} out of range 1..{n}")
    source = lib.first_table(prs.slides[pattern_slide - 1])
    count = 0
    for k in slides:
        for shape in prs.slides[k - 1].shapes:
            if getattr(shape, "has_table", False) and shape.has_table:
                lib.apply_table_style(shape._element, source)
                count += 1
    if not count:
        raise ValueError(f"no table on slides {slides}")
    prs.save(out)
    return count


def main(argv=None):
    lib.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("--pattern-slide", type=int, required=True)
    ap.add_argument("--slides", required=True, help="comma-separated 1-based slide numbers")
    ap.add_argument("-o", "--output", required=True)
    args = ap.parse_args(argv)
    try:
        count = restyle(args.deck, args.pattern_slide,
                        [int(s) for s in args.slides.split(",")], args.output)
    except ValueError as e:
        sys.exit(f"error: {e}")
    print(f"{args.output}: {count} table(s) restyled")


if __name__ == "__main__":
    main()
