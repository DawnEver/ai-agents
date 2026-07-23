# Step 00 — Create/select workspace

Runs once at the very start of the pipeline. Creates the workspace directory, `workspace.yaml`, and subdirectories for the review run.

## Inputs
- `<topic-name>` — argument to `/literature-review`

## Output

```
workspaces/<slug>/
  workspace.yaml          ← workspace metadata
  briefs/                 ← research brief drafts and approved versions
  runs/                   ← review run artifacts (one subdirectory per run)
  notes/                  ← free-form notes (not part of any run)
```

## Steps

1. **Derive slug** from the topic name (lowercase, non-alphanum → `-`, strip leading/trailing `-`).

2. **Check for existing workspace**: if `workspaces/<slug>/workspace.yaml` already exists, read it, confirm with the user that this is the right workspace, and skip to the resume table in SKILL.md. Otherwise continue.

3. **Create `workspaces/<slug>/workspace.yaml`**:
   ```yaml
   workspace_id: <slug>
   name: <original topic name>
   description: ""
   created_at: <ISO 8601 timestamp>
   ```

4. **Validate** the workspace file against `schemas/workspace.schema.json`:
   ```bash
   python scripts/schema_validate.py --file workspaces/<slug>/workspace.yaml --schema schemas/workspace.schema.json
   ```
   Fix any validation errors before proceeding.

5. **Create subdirectories**: `briefs/`, `runs/`, `notes/` under `workspaces/<slug>/`.

6. **User gate**: present the workspace layout to the user and confirm before proceeding.
   - Workspace ID, name, description
   - Directory structure created
   - Ask the user if they want to add a description or proceed

7. Proceed to step 01 (brief).

## Resume rule

If `workspaces/<slug>/workspace.yaml` already exists, skip workspace creation and proceed to the resume table. Do not overwrite an existing workspace.
