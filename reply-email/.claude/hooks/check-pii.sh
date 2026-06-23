#!/usr/bin/env bash
# Desensitization backstop: scan staged tracked files for obvious PII before commit.
# A safety net, not a substitute for the rules in AGENT.md → Desensitization.
# Install:  ln -sf ../../.claude/hooks/check-pii.sh .git/hooks/pre-commit
#   (or)    cp .claude/hooks/check-pii.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
set -u

# Run from the repo root so pathspecs resolve regardless of where the hook is invoked.
cd "$(git rev-parse --show-toplevel)" || exit 0

# Real data lives only in gitignored paths; staged tracked files should never contain PII.
staged=$(git diff --cached --name-only --diff-filter=ACM)
[ -z "$staged" ] && exit 0

# Allowlisted placeholders that are intentionally present in docs.
allow='example\.com|prof\.smith|\[Your Name\]|edcgghedcgg@gmail\.com'

# Patterns that signal real PII leaking into a committed file.
email_re='[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'

hits=0
for f in $staged; do
  [ -f "$f" ] || continue
  # Only the staged content, minus allowlisted placeholders.
  bad=$(git show ":$f" 2>/dev/null | grep -nE "$email_re" | grep -vE "$allow")
  if [ -n "$bad" ]; then
    echo "PII check: possible email address in staged file '$f':"
    echo "$bad"
    hits=1
  fi
done

if [ "$hits" -ne 0 ]; then
  echo
  echo "Commit blocked. Move real data into gitignored paths (ongoing/, archived/, style/profile.md)"
  echo "or add the placeholder to the allowlist in .claude/hooks/check-pii.sh."
  echo "Bypass intentionally with: git commit --no-verify"
  exit 1
fi
exit 0
