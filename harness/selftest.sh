#!/bin/bash
# 측정을 돌리기 전에 어댑터가 실제로 의도한 조건을 만드는지 확인한다.
#
# 왜 있나: 2026-09-21 에 --setting-sources '' 가 CLAUDE.md 로딩까지 막아서
# "팩 있음" 조건에 팩이 안 들어간 채로 15회가 돌았다. 실패가 아니라 침묵이라
# 로그 어디에도 안 나타났다. 이 스크립트가 그 침묵을 깨는 자리다.
#
# 이 레포의 6번 규칙(새 검사는 쓰기 전에 교정해라)을 하네스 자신에게 적용한 것.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CLEAN="$ROOT/harness/stubs/claude-clean.sh"
PACKED="$ROOT/harness/stubs/claude-pack.sh"
PACK="${FG_PACK:-$ROOT/pack/CLAUDE.md}"

# 팩 1번 규칙 제목과, 사용자 전역 규칙 제목. 전자는 팩에만, 후자는 어디에도 없어야 한다.
Q_PACK="너에게 주어진 지침에 'Count what actually ran' 이라는 제목의 규칙이 있나? YES 또는 NO 한 단어로만."
Q_USER="너에게 주어진 지침에 'Fire Logging' 또는 'Lane Routing' 이라는 제목의 규칙이 있나? YES 또는 NO 한 단어로만."

ask() { # ask <adapter> <question> ; 마지막 줄만 본다
  local wd; wd="$(mktemp -d)"
  ( cd "$wd" && printf '%s' "$2" | "$1" 2>&1 | tail -1 | tr -d '[:space:]' )
}

fails=0
check() { # check <라벨> <기대> <실제>
  if [ "$2" = "$3" ]; then printf "  ✓ %-34s %s\n" "$1" "$3"
  else printf "  ✗ %-34s 기대=%s 실제=%s\n" "$1" "$2" "$3"; fails=$((fails+1)); fi
}

echo "어댑터 교정 (4조합)"
check "베이스라인은 팩을 모른다"   NO  "$(ask "$CLEAN" "$Q_PACK")"
check "베이스라인은 사용자 규칙 모름" NO  "$(ask "$CLEAN" "$Q_USER")"
export FG_PACK="$PACK"
check "처치는 팩을 안다"          YES "$(ask "$PACKED" "$Q_PACK")"
check "처치도 사용자 규칙 모름"     NO  "$(ask "$PACKED" "$Q_USER")"

echo
if [ "$fails" -ne 0 ]; then
  echo "SELFTEST: FAIL ($fails 건) — 측정을 돌리지 마라. 지금 돌리면 조건이 의도와 다르다."
  exit 1
fi
echo "SELFTEST: PASS — 두 조건이 팩 하나만 다르다."
