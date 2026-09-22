---
name: pdf-front-matter-extraction-gotchas-2026-09-17
description: Why naive pymupdf front-matter parsing fails on conference PDFs — span whitespace, per-word line fragmentation, two-column interleaving, Unicode \b, ligatures and preposed accents
metadata:
  type: engineering
---

# Pulling title/abstract/keywords out of a PDF: the traps

`created: 2026-09-17, accessed: 2026-09-17`

Extracting front matter from a few hundred IEEE-style camera-ready PDFs with
pymupdf's `get_text("dict")`. Each of these cost real debugging time and none of
them raises an error — they just produce plausible-looking wrong text.

## Span-level traps

- **Whitespace lives in its own span.** `[s for s in line["spans"] if s["text"].strip()]`
  looks like harmless cleanup and is not: it drops the space spans, so
  `"".join(...)` welds every word together (`LifeCycleSustainability…`). Join the
  *unfiltered* spans for text and filter only when deriving size/font.
- **A PDF that positions each word separately makes pymupdf emit one "line" per
  word.** A label then arrives as `Index` / `Terms—High-speed` / `electrical` …
  as five separate entries at the same `y`, and no per-line regex matches it.
  The plain-text view (`page.get_text()`) has the same problem, but there the
  fragments are one `\n` apart, so a pattern using `\s+` across the break works.
- **A real two-column layout interleaves the facing column into the front
  matter's y-range.** The body text beside the abstract sits at the same `y` as
  the abstract's own lines, so any contiguous walk stops at the first line it
  does not recognise — which is the abstract's own second line. Selecting by
  *style class* (font weight + size) and by *column position* works where
  contiguity cannot.
- **Merging same-`y` fragments by a gap threshold does not work.** On a justified
  line, inter-word gaps reach ~11pt; the column gutter can be as small as ~7pt.
  The two ranges overlap, so no single threshold separates "same line" from
  "next column". Prefer style/column selection over geometric merging.

## Character-level traps

- **Python's `\b` is Unicode-aware.** `\babstract` does not match `ΦAbstract`,
  because the Greek letter is a word character and leaves no boundary. Use a
  lookbehind — `(?<![A-Za-z])abstract` — when the label may carry a stray glyph.
- **Ligatures and smart punctuation make text unsearchable.** `ﬁ` `ﬂ` `ﬀ` and
  curly quotes/dashes must be folded to ASCII or a search for `significant`
  misses `signiﬁcant`. `NFKC` handles the ligatures and composes legitimate
  accents — which means **any combining mark surviving NFKC is a layout
  artefact**, not a real accent.
- **Some producers (PCTeX and friends) emit an accent as a standalone glyph
  *before* its vowel** — `S´uken´ık` for `Súkeník`, `Loˇs´ak` for `Lošák`. NFC
  cannot recompose those. Map each spacing accent to its combining mark and
  *swap the pair* so the mark follows the base letter, then normalise.
- **Line-break hyphenation must be healed.** Joining wrapped lines with a space
  turns `im-\nproved` into `im- proved`, which matches nothing. A hyphen
  followed by a lowercase continuation is a wrap, not a compound.
- **Superscript affiliation markers ride along on author names** (`Grosso1`), and
  a name line's trailing all-caps two-letter token is usually a province code,
  not a surname (`Belo Horizonte, MG`).

## Tooling note

`paper_pdf_ingest` (the `pdf` extra of cc-academia) does *full decomposition* —
markdown sections plus extracted figures. It is not a front-matter metadata
extractor; `extract_title_from_preamble` is the same line-heuristic family as
the plugin's own, with the same weaknesses. Do not reach for it to pull
title/abstract/keywords.

The plugin's `src/academia/ingest/pdf.py` holds the reusable name heuristics
(`_looks_like_a_name`, `_clean_name`) and a text-only `parse_front_matter` that
is worth keeping as a fallback path — it reads the abstract well on IEEE
layouts and falls over on the author block and the keyword line.
