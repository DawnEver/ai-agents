# Step 04 — Fanout 锐评

Spawn one reviewer per angle **in parallel** via the `paper-review-fanout` workflow.

## Inputs
- `ongoing/<slug>/2-review/angles.md` (chosen angles + optional router overrides)
- `ongoing/<slug>/2-review/summary.md`, `ongoing/<slug>/2-review/literature.md` (if present)
- `1-paper-text/paper.md`, `1-paper-text/md/`, `1-paper-text/img/`, `1-paper-text/INDEX.md`
- `ongoing/<slug>/review-config.md` (for `lang:`)

## Output
- `ongoing/<slug>/2-review/critiques/<angle>.md` — one per angle

## Routing resolution

For each angle in `angles.md`:
1. If `Router override:` is non-empty, use it.
2. Else use the agent's frontmatter `router:` field.

| Router value | Provider | How invoked |
|--------------|----------|-------------|
| `sonnet-vision` | claude (Sonnet) | Direct via `agentType: reviewer-<angle>` inside the workflow |
| `takeover-codex` | codex | Workflow agent → `mcp__plugin_takeover_takeover__call_model` |
| `takeover-deepseek` | deepseek | Workflow agent → `mcp__plugin_takeover_takeover__call_model` |

## Execution

Read `angles.md` and build the args:

```json
{
  "slug": "<slug>",
  "lang": "<en|zh from review-config.md>",
  "angles": [
    { "name": "novelty", "definition": "...", "provider": "claude", "model": "" },
    { "name": "methodology", "definition": "...", "provider": "deepseek", "model": "deepseek-v4-pro" }
  ]
}
```

Map router → provider: `sonnet-vision` → `claude`, `takeover-codex` → `codex`, `takeover-deepseek` → `deepseek`.

**Before spawning, tell the user**: "Launching <N> reviewers in parallel via workflow — results will arrive in ~2–5 minutes."

Then invoke the workflow:

```
Workflow({ name: "paper-review-fanout", args: { slug, lang, angles } })
```

The workflow handles:
- Parallel execution of all reviewers via `parallel()`
- Direct Sonnet reviewers via `agentType: reviewer-<angle>` (reads files from disk)
- MCP-takeover reviewers via relay agent → `call_model` (inlines paper content)
- Structured output validation via schema
- Writing critiques to `critiques/<angle>.md`

## After fanout

Wait for the workflow to complete. Check every expected `2-review/critiques/<angle>.md` exists and is non-empty.

**Partial-recovery protocol**: if the workflow returns fewer results than angles, or critique files are missing:

1. **Retry missing reviewers** — re-invoke the workflow with only the failed angles (recommended).
2. **Skip missing angles** — proceed to step 05 with only the available critiques. Note in `critiques.md` which angles were skipped.
3. **Continue with partial (re-try later)** — write a placeholder file (e.g. `critiques/<angle>.md` containing `# <angle> — PENDING`) and proceed to step 05. The user can re-run via `/paper-review:rerun 04 <slug>`.

Do not silently enter step 05 with a partial set.
