"""Load .env from project root, then run zotero-mcp server. Stdlib only."""

import os
import sys
from pathlib import Path

# ── load .env ──────────────────────────────────────────────────────
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        os.environ.setdefault(key, val)

# ── apply runtime patches (pyzotero attachment filename bug) ───────
sys.path.insert(0, str(Path(__file__).resolve().parent))
import zotero_mcp_patch

zotero_mcp_patch.apply()

# ── hand off to the real entry point ────────────────────────────────
from zotero_mcp.cli import main

sys.exit(main())
