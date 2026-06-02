# Step 01 — Clone & Metadata

## Parse & Validate

Extract `owner/repo` from the URL. Supported formats:
- `https://github.com/owner/repo`
- `https://github.com/owner/repo.git`
- `owner/repo`

Derive the slug: lowercased, `--` replacing `/` (e.g., `facebook--react`).
If the URL is invalid, tell the user and stop.

Create the working directory:
```bash
mkdir -p "ongoing/<slug>/1-research" "ongoing/<slug>/2-draft" "ongoing/<slug>/3-final"
```

Determine target platforms:
- If user specifies one: `xiaohongshu`, `wechat`, `zhihu`, or `twitter` → generate for that only
- If no platform specified → generate for ALL four

## Clone or Update the Repo

```bash
# If NOT exists:
git clone --depth 50 --single-branch https://github.com/owner/repo.git repos/<slug>
# If clone FAILS: report the error clearly and stop. Common causes: private repo, renamed, network.

# If EXISTS:
cd repos/<slug> && git pull --depth 50 origin $(git branch --show-current) 2>&1
# If pull FAILS (conflicts, detached HEAD): warn user, proceed with existing copy.
```

## Quick Metadata (gh)

```bash
gh repo view owner/repo --json name,description,url,stargazerCount,primaryLanguage,topics,forkCount,createdAt,pushedAt 2>&1
```
If `gh` fails or is not installed: use WebFetch on `https://github.com/owner/repo` as fallback. Warn user that `gh` is preferred for richer metadata.
