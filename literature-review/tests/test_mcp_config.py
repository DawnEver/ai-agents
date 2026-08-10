"""Regression tests for the Zotero MCP server contract."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from literature_review.export.zotero import MCP_ARGS


ROOT = Path(__file__).resolve().parent.parent
SERVER_REQUIREMENT = "zotero-mcp-server[semantic,pdf]==0.6.3"


def test_mcp_clients_pin_the_compatible_server_release():
    claude = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))
    codex = tomllib.loads((ROOT / ".codex/config.toml").read_text(encoding="utf-8"))

    assert SERVER_REQUIREMENT in claude["mcpServers"]["zotero"]["args"]
    assert SERVER_REQUIREMENT in codex["mcp_servers"]["zotero"]["args"]
    assert "zotero-mcp-server==0.6.3" in MCP_ARGS
