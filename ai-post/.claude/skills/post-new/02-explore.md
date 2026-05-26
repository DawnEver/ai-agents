# Step 4: Deep Explore

## 4a: Project overview

```bash
ls -la repos/<slug>/
```
Read these if they exist: `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `LICENSE`.

## 4b: Source code structure

Use Glob to map source files and identify the architecture pattern, entry points, and dependencies. Check for package manifests (`package.json`, `Cargo.toml`, `go.mod`, `requirements.txt`).

## 4c: Implementation details

Read the main entry point, core library API, example/demo code, and key test files. Look for clever patterns, performance tricks, elegant API design.

## 4d: Recent activity

```bash
cd repos/<slug> && git log --oneline -20
```
