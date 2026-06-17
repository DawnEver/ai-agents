# Step 02 — Deep Code Exploration

Explore the cloned repo and write structured exploration notes.

## Inputs
- `repos/<repo-slug>/` — cloned repo from step 01

## Output
- `ongoing/<slug>/1-research/repo-exploration.md` — organized exploration findings

## Steps

### 1. Project overview

```bash
ls -la repos/<repo-slug>/
```
Read these if they exist: `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `LICENSE`.

### 2. Source code structure

Use Glob to map source files and identify the architecture pattern, entry points, and dependencies. Check for package manifests (`package.json`, `Cargo.toml`, `go.mod`, `requirements.txt`).

### 3. Implementation details

Read the main entry point, core library API, example/demo code, and key test files. Look for clever patterns, performance tricks, elegant API design.

### 4. Recent activity

```bash
cd repos/<repo-slug> && git log --oneline -20
```

### 5. Write exploration notes

Write `ongoing/<slug>/1-research/repo-exploration.md` with all findings organized under clear headings. This file feeds step 03 (market research) and step 04 (analysis).

## Resume

If `ongoing/<slug>/1-research/repo-exploration.md` is non-empty, skip this step.
