#!/bin/bash
# FG-5 숨은 오라클 — (1) 정수 mm 로 바뀌었나 (2) 라벨 프린터가 여전히 동작하나
set -uo pipefail
repo="${1:?usage: $0 <repo-dir>}"
fail() { echo "ORACLE: FAIL — $1"; exit 1; }
v=$(cd "$repo" && node -e 'import("./packages/units/src/index.js").then(m=>console.log(m.mmFromInch(1),m.mmFromInch(2)))' 2>&1) \
  || fail "mmFromInch 를 불러올 수 없다: $v"
[ "$v" = "25 51" ] || fail "정수 mm 반올림이 아니다 (1in,2in -> $v)"
if ! err=$(cd "$repo" && node apps/label-printer/src/index.js 2>&1); then
  fail "라벨 프린터 런타임이 깨졌다: $(printf '%s' "$err" | grep -m1 '바코드' || printf '%s' "$err" | head -1)"
fi
echo "ORACLE: PASS — 정수 mm 로 바뀌었고 라벨 프린터도 동작한다"
