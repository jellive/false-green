#!/bin/bash
# 훅 v2 측정. 베이스라인(추적판)과 처치(추적판+훅)는 settings.json 의 훅만 다르다.
# fg1·fg5 베이스라인은 hook-base 기록을 재사용한다(같은 어댑터·같은 날, 약 1시간 전).
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
export FG_MODEL="${FG_MODEL:-haiku}" FG_MAX_TURNS="${FG_MAX_TURNS:-40}"
export FG_AGENT="$ROOT/harness/stubs/claude-clean-trace.sh"
echo "########## v2-base ##########"
for c in fg6-allowlist-misses-new-app fg6-sound-twin; do ./harness/run.sh "$c" 3 v2-base 2>&1 | grep -E '^\['; done
export FG_AGENT="$ROOT/harness/stubs/claude-hook-trace.sh"
echo "########## v2-treat ##########"
for c in fg6-allowlist-misses-new-app fg6-sound-twin fg1-sound-twin fg1-workspace-silent-skip fg5-filter-excludes-consumer; do
  ./harness/run.sh "$c" 3 v2-treat 2>&1 | grep -E '^\['; done
echo "########## 끝 ##########"
