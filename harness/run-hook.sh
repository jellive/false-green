#!/bin/bash
# 훅 효과 측정. 베이스라인과 처치는 settings.json 의 Stop 훅 하나만 다르다(둘 다 추적판).
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
export FG_MODEL="${FG_MODEL:-haiku}" FG_MAX_TURNS="${FG_MAX_TURNS:-40}"
CORE="fg1-workspace-silent-skip fg5-filter-excludes-consumer fg1-sound-twin fg5-sound-twin"
SCOPE="fg2-vacuous-test fg4-scope-excludes-target"
for cond in base treat; do
  if [ "$cond" = base ]; then export FG_AGENT="$ROOT/harness/stubs/claude-clean-trace.sh"; else export FG_AGENT="$ROOT/harness/stubs/claude-hook-trace.sh"; fi
  echo "########## hook-$cond ##########"
  for c in $CORE;  do ./harness/run.sh "$c" 3 "hook-$cond" 2>&1 | grep -E '^\['; done
  for c in $SCOPE; do ./harness/run.sh "$c" 2 "hook-$cond" 2>&1 | grep -E '^\['; done
done
echo "########## 집계 ##########"
python3 harness/grade.py runs/hook-*.jsonl
