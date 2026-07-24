# Step 02 — Unified search & AI screening

AI 生成查询 → CLI 执行检索 → AI 批量筛选摘要。

## Steps

1. **Read the brief**. Extract concepts with `selected: true` and `role` in `[must, should, context]`.

2. **Generate Boolean queries** from concept taxonomy. Optionally delegate to `literature-query-reviewer` agent for review.

3. **Present queries** to user. Write to `workspaces/<slug>/queries.toml`.

4. **Probe** (optional but recommended):
   ```bash
   lit-review search --topic <slug> --probe-only
   ```
   Shows estimated hit counts. Adjust queries if needed, then re-run.

5. **Full search** — one command handles probe → search → normalize → dedupe → screening packet:
   ```bash
   lit-review search --topic <slug>
   ```

6. **AI screens all abstracts** in batches. Delegate to `literature-abstract-screener` agent.

7. **Import screening results**:
   ```bash
   lit-review import-screening --topic <slug> --batch <batch_001.jsonl> --batch <batch_002.jsonl> ...
   ```

8. **Report stats**: total, included, maybe, excluded. Show top candidates. Proceed to step 03.
