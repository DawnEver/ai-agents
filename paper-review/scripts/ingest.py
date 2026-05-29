#!/usr/bin/env python3
"""Thin backward-compat wrapper — delegates to paper_pdf_ingest package."""

import sys
from pathlib import Path

_src = Path(__file__).resolve().parent.parent / 'paper_pdf_ingest' / 'src'
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from paper_pdf_ingest.__main__ import main  # noqa: E402

if __name__ == '__main__':
    main()
