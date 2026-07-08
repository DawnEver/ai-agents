# Step 01 — Resolve Source & Metadata

The source is not always a GitHub repo. It can be a **GitHub URL**, a **local directory**
(an existing codebase, referenced in place — never copied), or a **local research report**
(a single `.pdf`/`.md`/`.txt`/… file to write *from*). This step detects which, resolves it,
and records the result in `ongoing/<slug>/1-research/source.md` — the pointer every later
step reads to find the raw material. See SKILL.md ## Source Kinds.

## Detect the Source Kind

Classify the argument (after the SKILL.md resume check has ruled out an existing `<slug>`):

1. **GitHub** — matches a GitHub URL or `owner/repo`:
   - `https://github.com/owner/repo` · `https://github.com/owner/repo.git` · `owner/repo`
2. **Pointer file** — the "text file that points somewhere else". A `.src` file is *always* a pointer.
   Any other small text file counts as a pointer **only if** its entire content is a single line that
   itself resolves to an existing path (so a real `report.txt` full of prose is NOT a pointer). Read
   that line, strip it, and re-classify **that** path as local-dir / local-file. A `repos/<slug>.src`
   file is this kind.
3. **Local path** — any other string that resolves to an existing path on disk (relative to the
   current working directory, or absolute):
   - resolves to a **directory** → `local-dir`
   - resolves to a **file** → `local-file` (research report)
4. Otherwise → tell the user the source is unrecognized (not a GitHub URL, not an existing path)
   and stop.

```bash
# After github/pointer are ruled out, resolve a local path robustly.
# Resolve the parent dir separately and TEST it — a bare `... || resolved=$src_arg`
# never fires (the assignment takes basename's exit status), and a missing parent
# would otherwise yield a bogus "/<basename>" rooted at /.
src_arg="$1"
dir="$(cd "$(dirname "$src_arg")" 2>/dev/null && pwd)"
if [ -n "$dir" ]; then resolved="$dir/$(basename "$src_arg")"; else resolved="$src_arg"; fi
if   [ -d "$resolved" ]; then kind=local-dir
elif [ -f "$resolved" ]; then kind=local-file
else echo "Unrecognized source: $src_arg (not a GitHub URL and not an existing path)" >&2; exit 1
fi
```

## Derive the Slugs

- **`<repo-slug>`** (cache/source key):
  - github → `owner--repo`, lowercased, `/`→`--` (e.g. `facebook--react`).
  - local-dir / local-file → the basename of the resolved path, lowercased, with every character
    outside the allowlist collapsed to `-` (e.g. `~/work/attention-report.pdf` → `attention-report`,
    `../my-cli/` → `my-cli`). If the user gave an explicit name, prefer it.
- **`<slug>`** (article-slug, keys the working dir): default `<slug> = <repo-slug>`. If
  `ongoing/<repo-slug>/` or any `archived/*/<repo-slug>/` already exists for a **different topic**,
  this is a separate article from the same source → `<slug> = <repo-slug>__<topic>`
  (short hyphenated topic from the user's angle). See SKILL.md ## Slug. Surface the chosen slug.

**Validate `<slug>` before using it in any path.** It must match `^[a-z0-9._-]+$` and contain no
`..` segment (guards against traversal like `../../etc/evil`). If it fails, lowercase and strip
every out-of-allowlist char, collapsing runs of `.` to a single `.`; if the result is empty or
still contains `..`, tell the user the slug is unusable and stop. (The **resolved source path**
above may be any absolute path — this validation is for the derived slug only, never the source.)

```bash
# Reject traversal / out-of-allowlist slugs before constructing paths.
case "$slug" in
  *..* | *[!a-z0-9._-]* | "") echo "Invalid slug: $slug" >&2; exit 1 ;;
esac
```

Create the working directory:
```bash
mkdir -p "ongoing/<slug>/1-research" "ongoing/<slug>/2-draft/v1"
```

Determine target platforms — **default is ALL platforms** (see `templates/_platform-registry.md`):
- **Default → generate for ALL platforms.** This is the default whenever the user does not
  *explicitly restrict* scope.
- Only narrow to a subset when the user gives an **explicit restriction** — e.g. "只发小红书" /
  "just Twitter" / "微信和知乎就行". A passing **format word** is NOT a restriction: "写一篇推文/帖子/文章"
  names a format, not a platform whitelist — still default to ALL platforms. When in doubt,
  generate all and let the user drop platforms at the brief gate.

## Fetch / Reference the Source

### kind: github
```bash
# If NOT exists:
git clone --depth 50 --single-branch https://github.com/owner/repo.git repos/<repo-slug>
# If clone FAILS: report the error clearly and stop. Common causes: private repo, renamed, network.

# If EXISTS:
cd repos/<repo-slug> && git pull --depth 50 origin $(git branch --show-current) 2>&1
# If pull FAILS (conflicts, detached HEAD): warn user, proceed with existing copy.
```
`resolved_path = repos/<repo-slug>`.

### kind: local-dir
Do **not** clone or copy — reference the directory in place. `resolved_path` = the absolute path.
Optionally leave a reusable one-line pointer in the shared cache so future articles can reference
the same local codebase (mirrors the clone cache), never copying the tree:
```bash
printf '%s\n' "<absolute-source-path>" > "repos/<repo-slug>.src"
```

### kind: local-file (research report)
Do **not** copy. `resolved_path` = the absolute path to the report file. The file itself is the
primary material — Step 02 reads it (PDF via the Read tool's `pages`, otherwise plain Read).

## Write the Source Pointer

Write `ongoing/<slug>/1-research/source.md` — the single record every later step resolves through:

```markdown
---
kind: github | local-dir | local-file
url: <github url>                 # kind: github only
path: <original argument as given>   # kind: local-* only
resolved_path: <absolute path or repos/<repo-slug> that Steps 02–04 read>
title: <human-readable name>
---
<optional one-line note on what this source is>
```

## Quick Metadata

- **github**: `gh repo view owner/repo --json name,description,url,stargazerCount,primaryLanguage,topics,forkCount,createdAt,pushedAt 2>&1`
  — if `gh` fails or is absent, fall back to WebFetch on `https://github.com/owner/repo` and warn.
- **local-dir**: no remote metadata. Note the directory name, top-level layout, and (if it is a git
  repo) `git -C <resolved_path> remote get-url origin` + recent log — otherwise "local, no remote".
- **local-file**: metadata comes from the document itself (title, author/publisher, date, source
  venue if stated) — captured in Step 02 ingest, not here.
