#!/usr/bin/env bash
# link-agent-data.sh — provision the bulk working data this repo does not track.
#
#   ./scripts/link-agent-data.sh            # link to synced data (auto-resolve)
#   ./scripts/link-agent-data.sh <path>     # link to synced data at <path>
#   ./scripts/link-agent-data.sh --local    # local-only: plain directories, no sync
#   ./scripts/link-agent-data.sh --status   # report what each path currently is
#
# WHY THIS EXISTS
#
# Each workspace writes bulk data — drafts, archives, PDF corpora, review runs. None of it
# is committed: it is large, and some of it (cc-docx/workspace) holds real contact emails
# and partner names. So a fresh clone has the code and the contracts but none of the data
# directories, and every workspace needs them to exist before it can write.
#
# Two ways to satisfy that:
#
#   --local   plain directories inside the repo. Nothing leaves the machine. This is the
#             right default for a single machine, and for anyone using the repo publicly.
#
#   (linked)  symlinks into a synced folder, e.g. <cloud>/Sync/agent-data. Use this when
#             several machines share one dataset. The data gets BACKUP and cross-machine
#             availability; the working tree still travels by git and never sits in cloud
#             storage — a sync daemon replicating .git/ corrupts the index and destroys the
#             reflog, which is what prompted this split on 2026-08-29.
#
# Both modes are gitignored and interchangeable: switch by re-running with the other flag.

set -euo pipefail

# Git Bash's `ln -s` does NOT create a symlink by default: for a directory it silently
# makes a recursive COPY. That is how 215M of agent-data ended up duplicated inside a
# Windows working tree while this script cheerfully printed LINK for every entry -- and
# because these paths are gitignored, `git status` stayed clean and hid it completely.
# A copy is worse than a failure here: it drifts from the cloud original, and
# cc-docx/workspace carries PII that is supposed to live in exactly one place.
#
# `nativestrict` makes ln FAIL instead of copying. Real failure is recoverable; a silent
# copy is not.
case "$(uname -s)" in
  MINGW* | MSYS* | CYGWIN*) IS_WINDOWS=1; export MSYS=winsymlinks:nativestrict ;;
  *) IS_WINDOWS=0 ;;
esac

# Create dest -> src as a genuine link, or return non-zero. On Windows a native symlink
# needs Developer Mode or an elevated shell; a directory junction needs neither, so fall
# back to one rather than leaving the user stuck.
make_link() {
  local src="$1" dest="$2"
  if ln -sfn "$src" "$dest" 2>/dev/null && [[ -L "$dest" ]]; then
    return 0
  fi
  if [[ $IS_WINDOWS -eq 1 ]]; then
    rm -rf "$dest"
    if cmd //c mklink //J "$(cygpath -w "$dest")" "$(cygpath -w "$src")" >/dev/null 2>&1; then
      [[ -L "$dest" || -d "$dest" ]] && return 0
    fi
  fi
  return 1
}

PATHS=(
  "ai-post/archived"
  "reply-email/archived"
  "manuscript-review/archived"
  "manuscript-review/ongoing"
  "literature-review/ongoing"
  "cc-docx/out"
  "cc-docx/workspace"
)

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mode="link"
explicit=""
for arg in "$@"; do
  case "$arg" in
    --local)  mode="local" ;;
    --status) mode="status" ;;
    -h|--help) sed -n '2,30p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) echo "unknown flag: $arg" >&2; exit 2 ;;
    *)  explicit="$arg" ;;
  esac
done

describe() {
  local dest="$1"
  if [[ -L "$dest" ]]; then
    echo "linked -> $(readlink "$dest")"
  elif [[ -d "$dest" ]]; then
    echo "local directory ($(find "$dest" -type f 2>/dev/null | wc -l | tr -d ' ') files)"
  else
    echo "missing"
  fi
}

if [[ "$mode" == "status" ]]; then
  echo "repo: $repo_root"
  for rel in "${PATHS[@]}"; do printf '  %-30s %s\n' "$rel" "$(describe "$repo_root/$rel")"; done
  exit 0
fi

if [[ "$mode" == "local" ]]; then
  echo "repo: $repo_root"
  echo "mode: local (plain directories, nothing synced)"
  echo
  for rel in "${PATHS[@]}"; do
    dest="$repo_root/$rel"
    if [[ -L "$dest" ]]; then
      echo "SKIP  $rel — currently a symlink; remove it first if you want a local directory"
      continue
    fi
    mkdir -p "$dest"
    printf 'DIR   %-30s ready\n' "$rel"
  done
  echo
  echo "Done. These paths are gitignored; nothing here will be committed."
  exit 0
fi

# ── linked mode ──────────────────────────────────────────────────────────────
# Resolve the data dir: explicit arg, $AGENT_DATA_DIR, then the sibling of the config
# sync payload (~/.claude/sync-dir names it), which is where it lives on this fleet.
resolve_data_dir() {
  [[ -n "$explicit" ]] && { echo "$explicit"; return; }
  [[ -n "${AGENT_DATA_DIR:-}" ]] && { echo "$AGENT_DATA_DIR"; return; }
  if [[ -f "$HOME/.claude/sync-dir" ]]; then
    local payload; payload="$(tr -d '\n' < "$HOME/.claude/sync-dir")"
    [[ -n "$payload" ]] && { echo "$(dirname "$payload")/agent-data"; return; }
  fi
  echo ""
}

DATA="$(resolve_data_dir)"

if [[ -z "$DATA" || ! -d "$DATA" ]]; then
  echo "ERR  no synced agent-data directory found${DATA:+: $DATA}" >&2
  echo >&2
  echo "     If you sync data across machines, pass the path or set AGENT_DATA_DIR:" >&2
  echo "       ./scripts/link-agent-data.sh \"<cloud>/Sync/agent-data\"" >&2
  echo >&2
  echo "     If you only use this repo on one machine, you do not need any of that:" >&2
  echo "       ./scripts/link-agent-data.sh --local" >&2
  exit 1
fi

echo "repo: $repo_root"
echo "data: $DATA"
echo

missing=0
for rel in "${PATHS[@]}"; do
  src="$DATA/$rel"
  dest="$repo_root/$rel"

  if [[ ! -e "$src" ]]; then
    printf 'SKIP  %-30s (no data at %s)\n' "$rel" "$src"
    missing=$((missing + 1))
    continue
  fi

  # Never clobber real content: only replace an existing symlink, or create a new one.
  if [[ -e "$dest" && ! -L "$dest" ]]; then
    printf 'SKIP  %-30s (real directory here — move it aside first)\n' "$rel"
    # An older version of this script left copies exactly here (and --local makes them on
    # purpose). Say so, but never delete: only a diff against the source can tell a stale
    # copy from unsaved work.
    printf '      if this is a copy left by an older run, compare it with\n'
    printf '      %s and remove it once they match\n' "$src"
    missing=$((missing + 1))
    continue
  fi

  mkdir -p "$(dirname "$dest")"
  if ! make_link "$src" "$dest"; then
    printf 'ERR   %-30s could not create a link\n' "$rel" >&2
    printf '      Enable Developer Mode (Windows Settings > For developers), run elevated,\n' >&2
    printf '      or use --local if this machine does not need synced data.\n' >&2
    missing=$((missing + 1))
    continue
  fi
  # Assert rather than assume: printing LINK over a copy is the bug this replaces.
  if [[ ! -L "$dest" && ! $(readlink -f "$dest") == "$(readlink -f "$src")" ]]; then
    printf 'ERR   %-30s is a copy, not a link — refusing to report success\n' "$rel" >&2
    missing=$((missing + 1))
    continue
  fi
  printf 'LINK  %-30s -> %s (%s files)\n' "$rel" "$src" "$(find -L "$dest" -type f 2>/dev/null | wc -l | tr -d ' ')"
done

echo
if [[ $missing -gt 0 ]]; then
  echo "Done with $missing skipped — those workspaces have no synced data yet."
  echo "Create them locally instead with: ./scripts/link-agent-data.sh --local"
fi
echo "\`git status\` should be clean — these paths are gitignored."
