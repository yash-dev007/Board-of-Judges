#!/usr/bin/env bash
set -euo pipefail

# Defaults
PANEL=""
JUDGES_DIR=""
MAX_FILES=25
FAIL_ON="FAIL"

while [ $# -gt 0 ]; do
  case "$1" in
    --panel) PANEL="$2"; shift 2;;
    --judges-dir) JUDGES_DIR="$2"; shift 2;;
    --max-files) MAX_FILES="$2"; shift 2;;
    --fail-on) FAIL_ON="$2"; shift 2;;
    *) echo "unknown arg $1" >&2; exit 2;;
  esac
done

mkdir -p judgements

# Determine changed files
if [ -n "${GITHUB_BASE_REF:-}" ]; then
  git fetch origin "$GITHUB_BASE_REF" --depth=1 >/dev/null 2>&1 || true
  mapfile -t FILES < <(git diff --name-only "origin/$GITHUB_BASE_REF"...HEAD -- \
    ':!**/*.md' ':!**/*.txt' ':!**/*.lock' ':!**/*.toml' ':!**/*.yaml' ':!**/*.yml' | head -n "$MAX_FILES")
else
  mapfile -t FILES < <(git diff --name-only HEAD~1 HEAD | head -n "$MAX_FILES")
fi

if [ ${#FILES[@]} -eq 0 ]; then
  echo "No reviewable files in this diff."
  echo "verdict=PASS" >> "$GITHUB_OUTPUT"
  echo "report_path=" >> "$GITHUB_OUTPUT"
  exit 0
fi

EXTRA=()
[ -n "$PANEL" ]        && EXTRA+=(--panel "$PANEL")
[ -n "$JUDGES_DIR" ]   && EXTRA+=(--judges-dir "$JUDGES_DIR")

BOARD_VERDICT="PASS"
{
  echo "# Board of Judges — PR review"
  echo
  echo "Reviewed ${#FILES[@]} file(s)."
  echo
  echo "| File | Verdict | Score | Critical | Warnings |"
  echo "|------|---------|------:|---------:|---------:|"
} > judgements/summary.md

for f in "${FILES[@]}"; do
  [ -f "$f" ] || continue
  slug=$(echo "$f" | tr '/ ' '--')
  out="judgements/${slug}.json"
  md="judgements/${slug}.md"

  set +e
  boj judge "$f" "${EXTRA[@]}" --output "$out" --markdown "$md" --format json > /dev/null
  ec=$?
  set -e

  if [ ! -f "$out" ]; then
    echo "| $f | ERROR | — | — | — |" >> judgements/summary.md
    continue
  fi

  v=$(python -c "import json,sys; d=json.load(open(sys.argv[1])); print(d['synthesis']['board_verdict'])" "$out")
  s=$(python -c "import json,sys; d=json.load(open(sys.argv[1])); print(d['synthesis']['board_score'])" "$out")
  crit=$(python -c "import json,sys; d=json.load(open(sys.argv[1])); print(len(d['synthesis']['critical_issues']))" "$out")
  warn=$(python -c "import json,sys; d=json.load(open(sys.argv[1])); print(len(d['synthesis']['warnings']))" "$out")

  echo "| \`$f\` | $v | $s | $crit | $warn |" >> judgements/summary.md

  case "$v" in
    FAIL) BOARD_VERDICT="FAIL";;
    WARN) [ "$BOARD_VERDICT" != "FAIL" ] && BOARD_VERDICT="WARN";;
  esac
done

echo >> judgements/summary.md
echo "Board verdict: **${BOARD_VERDICT}**" >> judgements/summary.md

echo "verdict=${BOARD_VERDICT}" >> "$GITHUB_OUTPUT"
echo "report_path=judgements/summary.md" >> "$GITHUB_OUTPUT"

# Exit code depends on fail_on policy
case "$FAIL_ON" in
  FAIL) [ "$BOARD_VERDICT" = "FAIL" ] && exit 1 ;;
  WARN) [ "$BOARD_VERDICT" != "PASS" ] && exit 1 ;;
  PASS) [ "$BOARD_VERDICT" != "PASS" ] && exit 1 ;;
esac
exit 0
