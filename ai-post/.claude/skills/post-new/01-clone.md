# Step 1-3: Clone & Metadata

## Step 1: Parse & Validate

Extract `owner/repo` from the URL. Supported formats:
- `https://github.com/owner/repo`
- `https://github.com/owner/repo.git`
- `owner/repo`

Derive the slug: lowercased, `--` replacing `/` (e.g., `facebook--react`).
If the URL is invalid, tell the user and stop.

Determine target platforms:
- If user specifies one: `xiaohongshu`, `wechat`, `zhihu`, or `twitter` → generate for that only
- If no platform specified → generate for ALL four

## Step 2: Clone or Update the Repo

```bash
# If NOT exists:
git clone --depth 50 --single-branch https://github.com/owner/repo.git repos/<slug>
# If clone FAILS: report the error clearly and stop. Common causes: private repo, renamed, network.

# If EXISTS:
cd repos/<slug> && git pull --depth 50 origin $(git branch --show-current) 2>&1
# If pull FAILS (conflicts, detached HEAD): warn user, proceed with existing copy.
```

## Step 3: Quick Metadata (gh)

```bash
gh repo view owner/repo --json name,description,url,stargazerCount,primaryLanguage,topics,forkCount,createdAt,pushedAt 2>&1
```
If `gh` fails or is not installed: use WebFetch on `https://github.com/owner/repo` as fallback. Warn user that `gh` is preferred for richer metadata.
