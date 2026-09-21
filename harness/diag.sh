#!/bin/bash
# 원인 판별용 측정. 추적판 어댑터로 돌려 도구 호출까지 남긴다.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
N="${FG_N:-2}"
CASES="fg1-workspace-silent-skip fg2-vacuous-test fg4-scope-excludes-target"
export FG_MAX_TURNS="${FG_MAX_TURNS:-40}" FG_PACK="$ROOT/pack/CLAUDE.md"

run() { # run <label> <model> <adapter>
  export FG_MODEL="$2" FG_AGENT="$ROOT/harness/stubs/$3"
  echo "########## $1 ##########"
  for c in $CASES; do ./harness/run.sh "$c" "$N" "$1" 2>&1 | grep -E '^\['; done
}
run diag-haiku-pack    haiku  claude-pack-trace.sh
run diag-sonnet-nopack sonnet claude-clean-trace.sh
run diag-sonnet-pack   sonnet claude-pack-trace.sh
echo "########## 집계 ##########"
python3 harness/grade.py runs/diag-*.jsonl
