# cc-slides — Agent Operating Notes

Template-faithful slide decks (PowerPoint `.pptx`) built from a declarative spec, verified by
rendering. Read this before touching scripts or running the pipeline.

## Why this shape

A slide is a 2-D arrangement, not a text flow: meaning lives in *where* boxes sit as much as in
what they say. So the authoritative working copy is a **spec** (`deck.toml`) that places content
into **patterns** — slides of the user's own template reused as layouts — never a Markdown
transcript of geometry. Agents cannot see a deck they have written, so **every build is rendered
and looked at**. Markdown appears only for wording edits of an existing deck (`slides2md` /
`md2slides`), where geometry is left untouched.

## The contract (what the scripts promise)

### `inspect_slides.py <deck.pptx> [--slides 3,19] [--json]`

- Lists slide size, layouts, and every shape: kind, geometry (inches), text, and **slot label**.
- Slot labels are the fill order `build_slides.py` uses: `title`, `image[i]`, `text[i]`,
  `table[i]`, numbered in **reading order** (rows top→bottom — a shape joins a row when its top is
  within half a height of the row's first shape — then left→right). Shapes are listed in z-order.
- Kinds: `title`, `footer` (slide number / date / footer placeholders), `picture`, `table`,
  `text` (non-empty text frame), `static` (everything else, incl. groups and empty boxes).

### `build_slides.py <deck.toml> [output.pptx]`

- Opens the template read-only; writes a **new** file (default
  `<spec dir>/out/<template-stem>-<yyMMdd>.pptx`). Refuses to write over the template.
- Per `[[slides]]` entry:
  - `keep = N` → template slide N, unchanged, at this position.
  - `pattern = "name"` → a new slide on the pattern slide's layout. Every pattern shape is
    re-created in z-order: slots are filled from `title` / `images` / `texts` / `tables`;
    `static` and `footer` shapes are copied verbatim with their relationships (images, links,
    charts, SmartArt). Hyperlinks to *other slides* are removed — the target may be dropped, and
    keeping the link would smuggle that slide back into the package.
- Images: `contain` (default; aspect kept, centred in the slot box), `cover` (fills the box,
  symmetric crop), `stretch` (explicit opt-in to distortion). `""` leaves a slot empty.
- Text: replaces the slot's paragraphs keeping the first paragraph's paragraph/run formatting;
  two leading spaces per indent level; `**bold**`; `\n` separates paragraphs.
- Tables: row count follows the spec (extra rows copy the last row), columns are fixed.
- **Unfilled slots are dropped** — template content never leaks into generated slides.
- More items than slots, unknown pattern, missing file, out-of-range slide → hard error.
- Template slides not listed with `keep` (including pattern slides) are removed.
- Shape ids are renumbered per slide (unique); connector end-points follow their shapes.

### `lint_slides.py <deck.pptx> [--strict]`

- Errors (exit 1): `distorted-image` (>1 % from source pixel aspect after crop), `off-slide`.
- Warnings (exit 1 only with `--strict`): `overlap` (>2 % of the smaller box), `empty-placeholder`,
  `text-overflow` (character-count estimate; skipped when the box has shrink-on-overflow).
- A floor, not a verdict. Overlap inherited from the user's own pattern is legitimate — report it,
  don't "fix" the user's layout unasked.

### `preview_slides.py <deck.pptx> [out_dir] [--dpi 80] [--columns 3]`

- Microsoft PowerPoint exports a PDF (`powerpoint.py`), Ghostscript rasterises it to
  `slide-NN.png`, and `contact.png` tiles all slides. Default out_dir
  `<deck dir>/preview/<deck stem>/`. Read `contact.png` first.

### `to_pdf.py <deck.pptx> [output.pdf]` — on demand only

### `slides2md.py <deck.pptx> [out.md]` / `md2slides.py <deck.md> <source.pptx> [out.pptx]`

- Wording loop for an existing deck. Every text shape / table / notes becomes a block headed by
  `<!-- s<slide_id>/<shape_id> -->` (the round-trip map — never edit or reorder anchors).
- Inside blocks: `<br>` = line break within a paragraph; in table cells `<p>` = paragraph break;
  a content line that looks like structure (`## Slide`, `<!--`, `\`) is escaped with a leading `\`.
- `md2slides` patches text back by anchor, preserving geometry and first-run formatting; tables
  may change row count. Unknown anchor → error; text outside anchors → ignored with a warning.
- Verify: `slides2md` of the output equals the edited md (except the source-name header line).

## Renderer notes (PowerPoint)

- **macOS sandbox.** PowerPoint cannot read `/tmp` or arbitrary paths ("PowerPoint can't read …"
  dialog), and scripted `open` fails with `-9074`. `powerpoint.py` stages each deck in
  `~/Library/Containers/com.microsoft.Powerpoint/Data/tmp/cc-slides/<token>/` under a unique file
  name, opens it with `open -g -a`, saves as PDF through an HFS path, copies back, closes, and
  deletes the staging dir. Don't bypass this.
- AppleScript `save as PNG` silently writes nothing — hence PDF + Ghostscript.
- PowerPoint AppleScript has no `whose` filtering (`-1750`); iterate presentations by index.
- Windows: COM via pywin32 (`SaveAs(pdf, 32)`). Other OSes: LibreOffice fallback (lower fidelity).
- Previewing opens and closes the deck in PowerPoint in the background; tell the user before the
  first preview of a session.

## Hard rules

1. The template is read-only input; the spec (or edited md) is authoritative; never hand-edit a
   generated `.pptx` and then rebuild over it.
2. After every build: `lint` then `preview`, and **look at `contact.png`** before reporting.
3. Images keep their aspect unless the user asked otherwise (`contain` / `cover`).
4. Don't invent titles, captions or conclusions. Use names that follow from the inputs (file
   names, the user's words); mark anything uncertain and ask.
5. PDF last, never first. The deliverable is the `.pptx` unless the user asks for PDF.

## Data layout

- `workspace` links to the synced `agent-data/cc-slides` root (see `../scripts/link-agent-data.sh`);
  it is never committed.
- Active tasks: `workspace/ongoing/<yyMMdd>-<slug>/` with `deck.toml`, `project.toml`
  (template, iteration, outputs), `src/` (template copies), `figures/` (inputs), `out/`
  (built decks, `out/preview/`). Completed tasks move intact to
  `workspace/archived/<yyMMdd>/<same-slug>/`.

## Tests

`python3 -m unittest discover -s tests` — synthetic templates only (no real/branded deck is
committed). `CC_SLIDES_POWERPOINT=1` additionally drives real PowerPoint.

## Known limits

Leading spaces in text are read as indent levels (two per level). Fields (slide number, date)
inside a *text slot* become plain text once filled. Text inside group shapes and charts are not slots (copied as static; a copied chart shares its
data part with the template's chart). `text-overflow` is an estimate — the preview is the truth.
