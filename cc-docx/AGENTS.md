# cc-docx — Agent Operating Notes

This project is a Word ↔ Markdown round-trip harness. Read this before touching scripts or running the pipeline.

## The contract (what the scripts promise)

### `docx2md.py <input.docx> [output.md]`

- Transcribes **all** body content in document order: paragraphs, lists, tables, section breaks. Headers/footers are captured as blockquotes at the top.
- Writes an invisible bookmark pair (`ccx1`, `ccx2`, …) around **every** body block in the input docx (paragraphs, tables) so the render pass can find them again. Bookmarks are invisible in Word (View ▸ Bookmarks is off by default).
- Emits `<!-- ccxN -->` on its own line before each block in the md — these are the round-trip map. **Do not delete or reorder them.**
- Tables: merged cells are expanded into an *effective matrix* (content repeated in spanned positions) so md and docx map 1:1 positionally. Rendered with `||` column separators on the header rule line (see tables below) — actually plain `|` markdown tables.
- Inline formatting: `**bold**`, `*italic*`, `` `code` ``, `[text](url)`, `==highlight==` (yellow highlight in Word; `==**text**==` combines highlight + bold). Both directions round-trip. `w:ins` (track-changes) runs are read back as plain text — the revision layer lives only in the docx.
- **Idempotent**: running twice on the same docx is safe (existing `ccx*` bookmarks are skipped, blocks already anchored keep their ids; new blocks get new ids).
- Never modifies the input docx except adding bookmarks. If you need a pristine original, keep a copy.

### `md2docx.py <input.md> <template.docx> [output.docx] [--track-changes]`

- Reads the **original** template (must still contain the `ccx*` bookmarks — use the copy that docx2md anchored, or the workflow breaks).
- Walks md blocks in order; for each anchored block it replaces the docx block's content:
  - paragraph → runs replaced (inline md parsed), paragraph style preserved
  - table → row count synced (extra rows appended by deep-copying the last row's XML; excess dropped), then every effective cell filled from the md
  - unanchored block → inserted **after the previous anchored block** (same document position where you wrote it in the md)
- Headings: anchored headings keep their original Word style; new unanchored headings map md `#`-level → Heading 1–6.
- Run-boundary spaces are preserved via `xml:space="preserve"` (without it Word silently drops spaces between runs — "adding ==GBP 200,000== by" renders as "addingGBP 200,000by").
- `--track-changes` (review mode): rewritten blocks are wrapped in `w:ins` revision elements (author "AI Agent") so the user can accept/reject AI-added content in Word's Review pane. Blocks whose md content equals the template's current text are left untouched — no revision, and the template's own formatting (e.g. design highlights) survives. Unchanged detection normalises whitespace (double spaces, NBSP), curly quotes, and compares whole cells (template cells may split one sentence across paragraphs); a block is still treated as changed if the md adds bold (`**`) the template text doesn't carry (e.g. answer marks "Yes / **No**"). Consequence: re-extracting such a doc may surface template-intrinsic formatting (highlight marks, NBSP) that the md doesn't carry — expected, not a bug.
- Writes a **new** output file. Never writes over the template. Default output name is `<md-project>/out/<stem>-<yyMMdd>.docx`, beside the authoritative Markdown project's other files; pass an explicit output path to override.

### `to_pdf.py <input.docx> [output.pdf]`

- Word COM via win32com (`Word.Application`, invisible). `FileFormat=17` (wdFormatPDF).
- On-demand only — do not run in the daily edit loop. Do not convert while the file is open in Word (COM lock failure).

## Hard rules

1. The md is the **authoritative working copy**; the template is read-only input.
2. Anchors (`<!-- ccxN -->` and the `ccx*` bookmarks) are part of the contract. Treat them like pointers, not comments.
3. If you hand-write a docx table's md row count differently from the original, `md2docx` will resize the table — intended for workplan-style step expansion. For fixed-layout forms (application form), keep rows.
4. Empty md cell/paragraph → cleared in the rendered docx. To *keep* original content, don't touch that block.
5. Verify renders: re-extract the output with `docx2md` and diff against the input md. Content should match exactly.
6. PDF last, never first. Ask yourself: does the user need a PDF, or a Word file? Default is Word.

## Data layout

- `workspace` is a local junction to the OneDrive data root; it is not source code and is never committed.
- Active tasks live in `workspace/ongoing/<yyMMdd>-<kebab-case-slug>/`.
- Completed tasks move intact to `workspace/archived/<yyMMdd>/<same-slug>/`.
- Keep templates in the task's `src/`, authoritative Markdown and `project.toml` in the task root, and rendered DOCX/PDF files in that task's `out/`. There is no repository-level `out/`.

## Common failure modes

- **"anchor not found"**: template was re-exported/re-downloaded after anchoring. Re-run `docx2md` on the fresh template (or copy bookmarks by editing the same file).
- **Run-level formatting lost on replaced paragraphs**: patch-back replaces runs; character-level formatting from the original paragraph (e.g. a bold label word inside an answer slot) is not preserved — put emphasis in the md instead.
- **Word open on the file** → `to_pdf.py` fails with a COM error; close Word first.
