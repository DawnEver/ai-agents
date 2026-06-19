# Step 01 — Clone & Metadata

## Parse & Validate

Extract `owner/repo` from the URL. Supported formats:
- `https://github.com/owner/repo`
- `https://github.com/owner/repo.git`
- `owner/repo`

Derive the **`<repo-slug>`**: lowercased, `--` replacing `/` (e.g., `facebook--react`). This keys the shared clone cache `repos/<repo-slug>/`.

Derive the **`<slug>`** (article-slug, keys the working dir):
- Default `<slug> = <repo-slug>`.
- If `ongoing/<repo-slug>/` or any `archived/*/<repo-slug>/` already exists for a **different topic**, this is a separate article from the same repo → set `<slug> = <repo-slug>__<topic>` (short hyphenated topic from the user's requested angle). See SKILL.md ## Slug. Surface the chosen slug to the user.

If the URL is invalid, tell the user and stop.

**Validate `<slug>` before using it in any path.** A slug derived from user input must match `^[a-z0-9._-]+$` and contain no `..` segment (guards against path traversal like `../../etc/evil`). If it fails, lowercase it and strip every character outside the allowlist, collapsing runs of `.` to a single `.`; if the result is empty or still contains `..`, tell the user the slug is unusable and stop.

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

Determine target platforms — **default is ALL platforms** (see `templates/_platform-registry.md` for the full list):
- **Default → generate for ALL platforms.** This is the default whenever the user does not *explicitly restrict* scope.
- Only narrow to a subset when the user gives an **explicit restriction** — e.g. "只发小红书" / "just Twitter" / "微信和知乎就行". A passing **format word** is NOT a restriction: "写一篇推文/帖子/文章" names a format, not a platform whitelist — still default to ALL platforms (the thread is one of the outputs, not the only one). When in doubt, generate all and let the user drop platforms at the brief gate.

## Clone or Update the Repo

```bash
# If NOT exists:
git clone --depth 50 --single-branch https://github.com/owner/repo.git repos/<repo-slug>
# If clone FAILS: report the error clearly and stop. Common causes: private repo, renamed, network.

# If EXISTS:
cd repos/<repo-slug> && git pull --depth 50 origin $(git branch --show-current) 2>&1
# If pull FAILS (conflicts, detached HEAD): warn user, proceed with existing copy.
```

## Quick Metadata (gh)

```bash
gh repo view owner/repo --json name,description,url,stargazerCount,primaryLanguage,topics,forkCount,createdAt,pushedAt 2>&1
```
If `gh` fails or is not installed: use WebFetch on `https://github.com/owner/repo` as fallback. Warn user that `gh` is preferred for richer metadata.
