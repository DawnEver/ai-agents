#!/usr/bin/env python3
"""Export a deck to PDF with Microsoft PowerPoint — on demand only, never in the edit loop.

Usage:
    python scripts/to_pdf.py <deck.pptx> [output.pdf]
"""
import argparse
import subprocess
import sys

import powerpoint


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("output", nargs="?")
    args = ap.parse_args(argv)
    try:
        print(powerpoint.export_pdf(args.deck, args.output))
    except (powerpoint.PowerPointError, subprocess.SubprocessError) as e:
        sys.exit(f"error: {e}")


if __name__ == "__main__":
    main()
