#!/bin/bash
# 전체 측정. 베이스라인과 처치는 어댑터만 다르고 나머지는 완전히 동일하다.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
N="${FG_N:-3}"
CASES="fg1-workspace-silent-skip fg1-sound-twin fg2-vacuous-test fg2-sound-twin fg3-stale-artifact fg3-sound-twin fg4-scope-excludes-target fg4-sound-twin"
export FG_MODEL="${FG_MODEL:-haiku}" FG_MAX_TURNS="${FG_MAX_TURNS:-40}"

# ★측정 전에 어댑터부터 교정한다. 실패하면 시작하지 않는다.
if [ "${FG_SKIP_SELFTEST:-0}" != "1" ]; then
  ./harness/selftest.sh || { echo "자기검사 실패 — 측정을 시작하지 않는다."; exit 1; }
  echo
fi

echo "########## 베이스라인 (팩 없음) ##########"
export FG_AGENT="$ROOT/harness/stubs/claude-clean.sh"; unset FG_PACK
for c in $CASES; do ./harness/run.sh "$c" "$N" baseline-nopack 2>&1 | grep -E '^\['; done

echo "########## 처치 (팩 있음) ##########"
export FG_AGENT="$ROOT/harness/stubs/claude-pack.sh" FG_PACK="$ROOT/pack/CLAUDE.md"
for c in $CASES; do ./harness/run.sh "$c" "$N" withpack 2>&1 | grep -E '^\['; done

echo "########## 대조표 ##########"
python3 harness/compare.py runs/*.jsonl
