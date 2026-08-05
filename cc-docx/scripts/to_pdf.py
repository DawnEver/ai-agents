# -*- coding: utf-8 -*-
"""docx → PDF via Word COM (invisible Word instance).

ON DEMAND ONLY — not part of the daily edit loop. Use when a PDF is
actually needed (uploads, final review). Fails if the file is open in Word.

Usage:  python scripts/to_pdf.py <input.docx> [output.pdf]
"""
import os
import sys


def convert(docx_path, pdf_path):
    import win32com.client  # pywin32
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0  # wdAlertsNone
    try:
        doc = word.Documents.Open(os.path.abspath(docx_path), ReadOnly=True)
        try:
            doc.SaveAs(os.path.abspath(pdf_path), FileFormat=17)  # wdFormatPDF
        finally:
            doc.Close(False)
    finally:
        word.Quit()
    print(f"pdf: {pdf_path}")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = os.path.abspath(sys.argv[1])
    if len(sys.argv) > 2:
        dst = os.path.abspath(sys.argv[2])
    else:
        dst = os.path.splitext(src)[0] + ".pdf"
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    convert(src, dst)


if __name__ == "__main__":
    main()
