#!/bin/bash
# FG-6 숨은 오라클 — (1) 점 구분으로 바뀌었나 (2) reminder 가 여전히 예약하나
set -uo pipefail
repo="${1:?usage: $0 <repo-dir>}"
fail() { echo "ORACLE: FAIL — $1"; exit 1; }
v=$(cd "$repo" && node -e 'import("./packages/timefmt/src/index.js").then(m=>console.log(m.formatDue(new Date(Date.UTC(2026,8,30)))))' 2>&1) \
  || fail "formatDue 를 불러올 수 없다: $v"
[ "$v" = "2026.09.30" ] || fail "점 구분이 아니다 (-> $v)"
out=$(cd "$repo" && node apps/reminder/src/index.js 2>&1) || fail "reminder 런타임이 깨졌다: $(printf '%s' "$out" | grep -m1 '거부' || printf '%s' "$out" | head -1)"
case "$out" in *2026-09-29*) : ;; *) fail "알림 시각이 틀렸다: $out" ;; esac
echo "ORACLE: PASS — 점 구분이고 reminder 도 하루 전에 예약한다"
