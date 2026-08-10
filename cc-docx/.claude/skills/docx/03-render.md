# Phase 3 — Render: markdown → docx (the daily delivery)

```bash
python scripts/md2docx.py <input.md> <template.docx> [output.docx]
```

Default output: `out/<template-stem>-<yyMMdd>.docx`. The renderer rejects an output path that resolves to the template itself.

## What happens

- The template must be the same file that `docx2md` anchored (it carries the `ccxN` bookmarks). Unknown anchors or paragraph/table kind mismatches fail before rendering; re-run Phase 1 on a fresh template when its anchors changed.
- Walks the md in order:
  - anchored paragraph → its runs are replaced with the parsed inline markdown, paragraph style preserved
  - anchored table → row count synced (rows appended by deep-copying the last row; excess dropped), then every grid cell filled from the md
  - unanchored block → inserted after the previous anchored block (heading level maps to Heading 1–6; tables get Table Grid style)
  - header/footer blockquotes → the anchored header/footer paragraph is replaced
- Anchors present in docx but absent from md are left untouched. Anchors referenced by md but absent from docx are errors.

## Verify (mandatory)

```bash
python scripts/docx2md.py out/X-<yyMMdd>.docx /tmp/x-re.md
diff <(sed '1d; s/ *$//' workspace/x.md) <(sed '1d; s/ *$//; s/<!-- ccx[0-9]* --> //' /tmp/x-re.md)
```

Expected diffs only: the transcript filename line, trailing whitespace, and `ccxN` anchors gained by previously-unanchored content. Anything else = bug, investigate before delivering.

## Then

Open the rendered docx in Word (or convert to PDF, Phase 4) and confirm layout is intact before sending it out.
