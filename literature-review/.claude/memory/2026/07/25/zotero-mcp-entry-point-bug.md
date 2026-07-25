---
name: zotero-mcp-entry-point-bug
description: uv tool run --from zotero-mcp-server resolves pyzotero-mcp to the wrong read-only server; correct entry point is zotero-mcp
created: 2026-07-25
metadata:
  type: reference
tags: [zotero, mcp, venv, gotcha]
---

## Problem

`zotero-mcp-server` (54yyyu/zotero-mcp on PyPI) depends on the `pyzotero` package.
`pyzotero` ships its own CLI scripts also named `pyzotero-mcp` / `pyzotero`. When
installed together, running `uv tool run --from zotero-mcp-server pyzotero-mcp`
**silently resolves to the wrong, read-only server** shipped by the `pyzotero`
dependency — not the full `zotero-mcp-server` package. uv even prints a warning
about this ("executable ... is available via the dependency `pyzotero`") but it's
easy to miss.

Symptom: MCP tools connect fine and read-side tools work (search, get_item,
list_collections), but there is no write toolset at all — `zotero_add_by_doi`,
`zotero_add_from_file`, `zotero_manage_collections` etc. don't exist on the
connected server, even though the README documents them.

## Fix

The correct entry point is **`zotero-mcp`** (maps to `zotero_mcp.cli:main`), not
`pyzotero-mcp`. Verify entry points directly instead of trusting instinct:

```bash
python -c "import importlib.metadata as m; [print(e.name, '->', e.value) for e in m.distribution('zotero-mcp-server').entry_points]"
# zotero-cli -> zotero_mcp.cli_standalone:main
# zotero-mcp -> zotero_mcp.cli:main
```

Verify the live tool list matches the README before wiring a client to it:

```bash
python -c "
from zotero_mcp import server
import asyncio
for t in asyncio.run(server.mcp.list_tools()):
    print(t.name)
"
```

Correct config (`.mcp.json` and any subprocess spawn args):

```json
{"mcpServers": {"zotero": {"command": "uv", "args": ["tool", "run", "--from", "zotero-mcp-server", "zotero-mcp", "serve", "--transport", "stdio"]}}}
```

## Where this landed

- `literature-review/.mcp.json`
- `literature-review/literature_review/export/zotero.py` (`MCP_ARGS`)
- Venv: `~/.local/share/lit-review-venv` (cross-platform pattern, matches manuscript-review)

## Lesson

When a package depends on another package that has overlapping CLI script names,
`uv tool run --from <outer-package> <script-name>` does NOT guarantee the script
comes from `<outer-package>` — it resolves by script name across the whole
dependency closure. Always verify entry_points and live tool/capability lists
after wiring a new MCP server, don't assume the README's tool names are what's
actually being served.
