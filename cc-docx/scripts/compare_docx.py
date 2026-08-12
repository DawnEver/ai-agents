# -*- coding: utf-8 -*-
"""Smart tracked-changes diff via Word's native Compare engine.

Uses Word.Application.CompareDocuments to produce a real document diff
(insertions = green underline, deletions = red strikethrough, moved text
= move markers, preserved text = untouched). Formatting changes are NOT
detected, so the intentional bullet re-nesting doesn't flood the diff.

Usage: python scripts/compare_docx.py <original.docx> <revised.docx> <output.docx>
"""
import os
import sys


def compare(orig_path, revised_path, output_path):
    import win32com.client  # pywin32
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0  # wdAlertsNone
    try:
        orig = word.Documents.Open(os.path.abspath(orig_path), ReadOnly=True)
        rev = word.Documents.Open(os.path.abspath(revised_path), ReadOnly=True)
        result = None
        try:
            # CompareDocuments(Original, Revised, Destination=New doc,
            #   Granularity=Word, CompareFormatting=False, ...) — rest default.
            result = word.CompareDocuments(
                orig, rev,
                2,     # wdCompareDestinationNew
                0,     # wdGranularityWordLevel
                False, # CompareFormatting
            )
            result.SaveAs2(os.path.abspath(output_path))
            print(f"tracked: {output_path}")
        finally:
            for doc in (rev, orig, result):
                if doc is None:
                    continue
                try:
                    doc.Close(False)
                except Exception:
                    pass
    finally:
        word.Quit()


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    orig, rev, out = [os.path.abspath(a) for a in sys.argv[1:4]]
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    compare(orig, rev, out)


if __name__ == "__main__":
    main()
