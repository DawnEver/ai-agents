# Options Menu — What would you like to do?

核心流水线完成后，后续能力作为选项菜单供用户自由选择。非强制、非线性、可组合。

## Available Options

### Deep-Read Papers
```bash
lit-review read --topic <slug> --paper <candidate_id> [--lens <name>]
```
Applies domain lens for domain-specific scrutiny. Produces `reading/<id>_card.json` + `reading/<id>_card.md`.

### Cross-Paper Synthesis
```bash
lit-review synthesize --topic <slug> [--paper <id1> --paper <id2>]
```
Compares all deep-read papers (or specified subset). Produces `notes/synthesis.md`.

### Export
```bash
lit-review export --topic <slug> [--format markdown|csv|bibtex|json] [--paper <id1> ...]
```
Exports paper cards in the requested format to `export/`.

### Statistics & Plots
```bash
lit-review stats --topic <slug> [--plots]
```
Summary statistics (candidates, screening breakdown, downloads, decomposed, deep-read). With `--plots`, generates year/venue distribution charts.

### Zotero Sync
Push paper metadata, PDFs, and reading notes to a Zotero collection. Requires Zotero binding in `workspace.toml`.

### Custom
Anything else — re-search with modified queries, add papers manually, compare specific papers, generate a summary report. Just ask.

## How it works

1. **Present the menu** after step 04 completes (or whenever the user asks).
2. **User picks** one or more options. Execute and return to menu.
3. **No forced sequence**. User can deep-read 2 papers, skip synthesis, export BibTeX, done.
4. **CLI commands exist for everything**. Agent can call them directly instead of micro-managing.
