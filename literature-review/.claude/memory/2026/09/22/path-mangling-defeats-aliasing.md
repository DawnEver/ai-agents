---
name: path-mangling-defeats-aliasing-2026-09-22
description: A dependency that rewrites spaces in a path cannot be fixed by pointing at a space-free alias, because resolve() undoes the alias; extract the needed content yourself instead
metadata:
  type: engineering
---

# When a dependency mangles a path, aliasing cannot rescue it

`created: 2026-09-22, accessed: 2026-09-22`

## Symptom

Every paper in a batch failed to decompose, with an error naming a path that
did not exist:

```
code=2: cannot open file '.../OneDrive_-_The_University_of_Nottingham/...'
```

The real directory has spaces; the path in the error has underscores. A file was
written under one name and reopened under another.

## Where it comes from

The decomposer hands the PDF to `pymupdf4llm.to_markdown(..., image_path=...)`.
That library derives extracted-image names from the source PDF's filename, and
its sanitiser replaces spaces with underscores. The write and the later re-open
disagree, so the only files it ever fails on are the ones whose path contains a
space — which means **the failure is a property of where the data lives, not of
the data**.

## Two fixes that look right and are not

Both are worth remembering precisely because each is the obvious first move.

1. **Point the data root at a space-free symlink.** The workspace had a
   symlinked alias into the same tree, with no spaces, and setting the
   configuration variable at it changed nothing. The library calls
   `resolve()` (or equivalent) on the path, and a symlink resolves to its
   target — the real, space-bearing location. `repair` likewise re-derives each
   stored path by scanning the disk, and the disk reports the real location.

   **The general rule: aliasing cannot fix path mangling, because resolving an
   alias is exactly the operation that undoes it.** If the consumer normalises
   paths, any indirection you add is removed before the consumer sees it.

2. **Re-run the state-rebuild command.** It rewrote the manifest faithfully and
   produced the same space-bearing paths, because that is where the files
   actually are.

## What worked

Extract the content directly, bypassing the dependency: a short script opening
each PDF with PyMuPDF and dumping `page.get_text("text")` to a file.

This is not a degradation *if you say what it costs*. The decomposer was
producing section segmentation and figures as well; a reading that needs the
prose only — a method-level reading of a formulation, say — does not need
either. Decide what the downstream task actually consumes before treating the
full pipeline as mandatory, and record what the substitute omits.

Print a size per item when you do this. A scanned, image-only document extracts
to near-zero characters, and without a visible count that reads as a clean
success rather than as an empty one.

## Corollary

Before building a workaround, find which component mangles the path and why.
Here the traceback named a path, not the culprit; the culprit was one call two
layers down, and knowing it is what distinguished "the data is unusable" from
"one library's filename sanitiser is".

## Files

- the third-party decomposer's `convert.py` — the `to_markdown(..., image_path=)`
  call, and a sibling `dest = out_dir / 'img' / 'flat' / img.name`
