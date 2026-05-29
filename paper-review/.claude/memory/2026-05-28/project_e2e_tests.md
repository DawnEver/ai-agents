---
name: e2e-tests
description: Tests reorganised into unit/ and e2e/ subdirs; hairpin PDF added; per-asset exact sizes tested
metadata:
  type: project
---

# Test directory structure

Reorganised from flat `tests/test_*.py` to:

```
tests/
  conftest.py        ← LONG_BODY, make_test_pdf, marker_available, _marker_skip
  data/
    ieee-conference.pdf    (git tracked, template PDF, LaTeX ground truth)
    wang-hairpin-2025.pdf  (gitignored — real paper data, copyright)
  unit/              ← 49 fast tests, ~0.5s, no real PDF
  e2e/
    conftest.py      ← run_full_pipeline(), module-scoped hairpin fixtures
    test_ieee_conference.py  (14 pass, marker skip)
    test_wang_hairpin.py     (67 pass, 18 skip / marker)
```

**gitignore**: `tests/data/*.pdf` except `ieee-conference.pdf`. Add new paper PDFs here.

## Module-scoped fixture pattern
`hairpin_out_pymupdf4llm` / `hairpin_out_marker` run the full pipeline ONCE per
session (not per test), reusing the tmp dir for all tests in that module.

## `paper_pdf_ingest.convert` import gotcha
`from paper_pdf_ingest import convert as m` → `m` is the function, not the module.
`__init__.py` shadows the submodule name. Use `sys.modules['paper_pdf_ingest.convert']`.

## wang-hairpin-2025 ground truth
- 9 sections; key: Introduction, II/scripting, III/interference, IV/check, V/conclusion
- 13 figures (Fig. 1-13); Fig. 12 is 2-column-wide (980×294 px)
- 3 tables (TABLE I, II, III)
- Eqs 1-12 in sec03, Eq 13 in sec04

**Per-asset sizes** (observed at 2×render, ±30 px tolerance):
see `_FIGURE_SIZES`, `_TABLE_SIZES`, `_EQ_SIZES` dicts in test_wang_hairpin.py.

## Known limitations in tests
- **Eq 8**: lead-in is inside a pymupdf4llm ```math``` block; non-deterministic.
  Test requires 11/12 equations (allows eq8 missing).
- **Eq 13**: not inserted inline (defining prose not captured). Test only checks
  that the IMAGE FILE was rendered.
- **Eq 5/6 order**: their definitions are in 2-column region not captured; they
  land at cross-reference positions. Test checks strict order for
  {1,2,3,4,7,9,10,11,12} and additionally 5<7 and 6<7.

## IEEE conference ground truth (unchanged)
1 figure (Figure 1, 341×297 px), 1 table (Table I), ~6 sections.
Title: "Conference Paper Title".
