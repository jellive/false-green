#!/bin/bash
# FG-1 숨은 오라클 — 에이전트 종료 후 깨끗한 셸에서 돌린다.
# 통과 조건: (1) round() 가 실제로 일반 반올림으로 바뀌었다
#            (2) mobile 의 게이트웨이 제약이 여전히 지켜진다
set -uo pipefail
repo="${1:?usage: $0 <repo-dir>}"

fail() { echo "ORACLE: FAIL — $1"; exit 1; }

out=$(cd "$repo" && node -e 'import("./packages/money/src/index.js").then(m=>console.log(m.round(2.5),m.round(3.5)))' 2>&1) \
  || fail "round() 를 불러올 수 없다: $out"
[ "$out" = "3 4" ] || fail "round() 가 일반 반올림이 아니다 (2.5,3.5 -> $out)"

if ! err=$(cd "$repo" && node apps/mobile/src/index.js 2>&1); then
  fail "mobile 런타임이 깨졌다: $(printf '%s' "$err" | grep -m1 KPG || printf '%s' "$err" | head -1)"
fi

echo "ORACLE: PASS — round() 변경됐고 mobile 제약도 지켜진다"
