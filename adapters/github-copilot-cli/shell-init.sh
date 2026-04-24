#!/usr/bin/env bash
# Board of Judges — shell integration for GitHub Copilot CLI / any POSIX shell

judge() {
  if [ -z "$1" ]; then
    echo "usage: judge <file> [--panel ...] [--solo ...] [--all]" >&2
    return 2
  fi
  boj judge "$@"
}

judge-all() {
  if [ -z "$1" ]; then
    echo "usage: judge-all <dir>" >&2
    return 2
  fi
  find "$1" -type f \( -name "*.py" -o -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.go" \) \
    -print0 | while IFS= read -r -d '' f; do
      echo "=== $f ==="
      boj judge "$f" --format terminal
    done
}

judge-pr() {
  local pr="${1:-$(gh pr view --json number -q .number 2>/dev/null)}"
  if [ -z "$pr" ]; then
    echo "No PR detected. Usage: judge-pr <pr-number>" >&2
    return 2
  fi
  mkdir -p judgements
  local stamp
  stamp="$(date +%Y-%m-%d-%H%M)"
  for f in $(gh pr diff "$pr" --name-only); do
    local slug
    slug="$(basename "$f" | tr ' /' '--')"
    boj judge "$f" \
      --markdown "judgements/${stamp}-pr${pr}-${slug}.md" \
      --output   "judgements/${stamp}-pr${pr}-${slug}.json" \
      --format terminal
  done
}
