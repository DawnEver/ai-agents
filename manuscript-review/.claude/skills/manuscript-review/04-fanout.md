# Step 04 — Fanout 锐评

Spawn one reviewer per angle **in parallel** via the `manuscript-review-fanout` workflow.

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

**If any angle uses MCP takeover (codex/deepseek)**, pre-read the paper text to pass as `paperSections` in args. This prevents the relay agent from reading paper files directly, closing a prompt-injection vector where paper content could influence relay behavior before it builds the downstream prompt (H2).

Pre-read steps:
1. Read `ongoing/<slug>/1-paper-text/paper.md` for title + abstract.
2. Read `ongoing/<slug>/1-paper-text/md/` — prioritize Method, Theory, Experimental Setup / Results sections. Skip appendices unless an angle specifically needs them.
3. Concatenate into a single string `paperSections`. Cap at ~50K words; note truncation if applied.
4. Add `paperSections` to the workflow args object.

If all angles use direct Sonnet (`provider: "claude"`), `paperSections` can be omitted — the reviewer agents read files from disk directly.

**Before spawning, tell the user**: "Launching <N> reviewers in parallel via workflow — results will arrive in ~2–5 minutes."

Then invoke the workflow:

```
Workflow({ name: "manuscript-review-fanout", args: { slug, lang, angles, paperSections } })
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
3. **Continue with partial (re-try later)** — write a placeholder file (e.g. `critiques/<angle>.md` containing `# <angle> — PENDING`) and proceed to step 05. The user can re-run via `/manuscript-review:rerun 04 <slug>`.

Do not silently enter step 05 with a partial set.
