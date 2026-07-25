#!/usr/bin/env bash
# Load .env and exec zotero-mcp from the shared lit-review venv.
set -a
cd "$(dirname "$0")/.." || exit 1
if [ -f .env ]; then
  # shellcheck disable=SC1091
  source .env
fi
set +a
VENV_PYTHON="$HOME/.local/share/lit-review-venv/Scripts/python.exe"
if [ ! -f "$VENV_PYTHON" ]; then
  VENV_PYTHON="$HOME/.local/share/lit-review-venv/bin/python3"
fi
exec "$VENV_PYTHON" -m zotero_mcp.cli serve --transport stdio
