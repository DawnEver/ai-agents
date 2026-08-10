#!/usr/bin/env bash
# Desensitization backstop: scan staged tracked files for PII AND sensitive
# project content before commit. Covers ALL repos under this agents root
# (installed as .git/hooks/pre-commit of the root repo).
# A safety net, not a substitute for the rules in each project's AGENTS.md.
#
# Install (after editing this file):
#   cp .claude/hooks/check-pii.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
set -u

# Run from the repo root so pathspecs resolve regardless of where the hook is invoked.
cd "$(git rev-parse --show-toplevel)" || exit 0

# Real data lives only in gitignored paths; staged tracked files should never contain it.
staged=$(git diff --cached --name-only --diff-filter=ACM)
[ -z "$staged" ] && exit 0

# Allowlisted placeholders that are intentionally present in docs.
allow='example\.com|prof\.smith|\[Your Name\]|edcgghedcgg@gmail\.com'

# Patterns that signal real PII leaking into a committed file.
email_re='[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'

# Sensitive project content (partner/client names, real people, project
# paths, registration numbers, private domains) lives in patterns.local
# NEXT TO THIS FILE — gitignored, so the hook itself stays commit-safe.
# Extend that file when a new project starts; without it, only emails are
# checked.
patterns_file="$(git rev-parse --show-toplevel)/.claude/hooks/patterns.local"
if [ -f "$patterns_file" ]; then
  sensitive_re=$(grep -vE '^\s*(#|$)' "$patterns_file" | paste -sd'|' -)
else
  sensitive_re=''
fi

hits=0
for f in $staged; do
  [ -f "$f" ] || continue
  # Only the staged content, minus allowlisted placeholders.
  bad=$(git show ":$f" 2>/dev/null | grep -nE "$email_re|$sensitive_re" | grep -vE "$allow")
  if [ -n "$bad" ]; then
    echo "PII/sensitive check: possible leak in staged file '$f':"
    echo "$bad" | head -20
    hits=1
  fi
done

if [ "$hits" -ne 0 ]; then
  echo
  echo "Commit blocked. Move real data into gitignored paths (workspace/, ongoing/, archived/)"
  echo "or add an allowlisted placeholder in .claude/hooks/check-pii.sh."
  echo "Bypass intentionally with: git commit --no-verify"
  exit 1
fi
exit 0
