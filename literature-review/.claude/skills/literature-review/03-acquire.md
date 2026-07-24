# Step 03 — PDF acquisition (script-first, batch)

纯脚本批量获取 PDF。Agent 只介入一次：分析认证需求。

## Core principle

**Agent analyzes auth once → User configures once → Script downloads all in batch.**

## Steps

1. **Build & review download queue**:
   ```bash
   lit-review acquire --topic <slug> --queue-only
   ```
   Shows queue at `workspaces/<slug>/download/download_queue.csv`. User reviews.

2. **Approve candidates** and download:
   ```bash
   lit-review acquire --topic <slug> --candidate-id <id1> --candidate-id <id2> ...
   ```
   If no `--candidate-id` is given, all `include` decisions are auto-approved.

3. **Analyze auth** (agent does this ONCE):
   - Which publishers need authentication?
   - What method? (cookie/session, API key, institutional proxy)
   - If browser login needed:
     ```bash
     lit-review login --profile ieee
     ```
     Profiles live at `%LOCALAPPDATA%/literature-review/browser-profiles/` — outside repo.

4. **Download with auth** (script handles all):
   ```bash
   lit-review acquire --topic <slug> --profile <profile-path>
   ```
   Sequential downloads with polite delays. All failures logged.

5. **Report**: X downloaded, Y failed, Z matched. Proceed to step 04.
