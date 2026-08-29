#!/usr/bin/env bash
# link-agent-data.sh — relink this working tree to the bulk data that lives outside it.
#
#   ./scripts/link-agent-data.sh [/path/to/agent-data]
#
# Why the split: this repo's working tree must NOT live in cloud storage — a sync daemon
# replicating .git/ corrupts the index and destroys the reflog (it did, on 2026-08-29).
# But some of the working data is not a git matter at all: it is large, partly PII-bearing,
# and deliberately never committed. That data wants BACKUP, which cloud storage is good at.
#
# So: the tree travels via GitHub, the data sits in <cloud>/Sync/agent-data/, and these
# gitignored symlinks join them. Run this after a fresh clone, or when the cloud path
# changes (different machine, different username — the fleet has both `linxu` and
# `ezxmb14`).

set -euo pipefail

LINKS=(
  "ai-post/archived"
  "reply-email/archived"
  "manuscript-review/archived"
  "manuscript-review/ongoing"
  "cc-docx/out"
  "cc-docx/workspace"
)

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Resolve the data dir: explicit arg, then $AGENT_DATA_DIR, then the sibling of the
# claude-config sync payload (~/.claude/sync-dir names it), then a plain guess.
resolve_data_dir() {
  [[ $# -gt 0 && -n "${1:-}" ]] && { echo "$1"; return; }
  [[ -n "${AGENT_DATA_DIR:-}" ]] && { echo "$AGENT_DATA_DIR"; return; }
  if [[ -f "$HOME/.claude/sync-dir" ]]; then
    local payload; payload="$(tr -d '\n' < "$HOME/.claude/sync-dir")"
    [[ -n "$payload" ]] && { echo "$(dirname "$payload")/agent-data"; return; }
  fi
  echo "$HOME/OneDrive/Sync/agent-data"
}

DATA="$(resolve_data_dir "$@")"

if [[ ! -d "$DATA" ]]; then
  echo "ERR  agent-data not found: $DATA" >&2
  echo "     Pass the path explicitly, or set AGENT_DATA_DIR." >&2
  exit 1
fi

echo "repo: $repo_root"
echo "data: $DATA"
echo

missing=0
for rel in "${LINKS[@]}"; do
  src="$DATA/$rel"
  dest="$repo_root/$rel"

  if [[ ! -e "$src" ]]; then
    printf 'SKIP  %-32s (no data at %s)\n' "$rel" "$src"
    missing=$((missing + 1))
    continue
  fi

  # Never clobber real content: only replace an existing symlink, or create a new one.
  if [[ -e "$dest" && ! -L "$dest" ]]; then
    printf 'SKIP  %-32s (real directory here — move it aside first)\n' "$rel"
    missing=$((missing + 1))
    continue
  fi

  mkdir -p "$(dirname "$dest")"
  ln -sfn "$src" "$dest"
  printf 'LINK  %-32s -> %s (%s files)\n' "$rel" "$src" "$(find -L "$dest" -type f 2>/dev/null | wc -l | tr -d ' ')"
done

echo
if [[ $missing -gt 0 ]]; then
  echo "Done with $missing skipped. Check the cloud client has finished downloading."
  exit 1
fi
echo "Done. \`git status\` should be clean — these paths are gitignored."
