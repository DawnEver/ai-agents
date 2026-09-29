# 05 — Reword an existing deck

For text-only changes to a deck that already exists (no layout changes):

```bash
python3 scripts/slides2md.py <task>/src/Deck.pptx <task>/deck.md
# edit wording in deck.md — keep every <!-- s<slide>/<shape> --> anchor line as is
python3 scripts/md2slides.py <task>/deck.md <task>/src/Deck.pptx      # → <task>/out/Deck-<yyMMdd>.pptx
python3 scripts/slides2md.py <task>/out/Deck-<yyMMdd>.pptx | diff - <task>/deck.md   # only line 1 may differ
```

- Indent = two spaces per bullet level; `**bold**`; tables may gain/lose rows, not columns.
- Text written outside an anchor is ignored (warning). New boxes or moved content → use deck.toml.
- Then run `04-verify.md` on the output (longer text may overflow).
