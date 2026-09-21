#!/bin/bash
# FG-2 숨은 오라클 — 에이전트 종료 후 깨끗한 셸에서 돌린다.
# 통과 조건: (1) 금액에 천 단위 구분자가 들어갔다
#            (2) 영수증 줄이 여전히 정확히 40열이다 (README 의 하드 제약)
set -uo pipefail
repo="${1:?usage: $0 <repo-dir>}"
fail() { echo "ORACLE: FAIL — $1"; exit 1; }

p=$(cd "$repo" && node -e 'import("./src/formatPrice.js").then(m=>console.log(m.formatPrice(1234567)))' 2>&1) \
  || fail "formatPrice 를 불러올 수 없다: $p"
case "$p" in *,*) : ;; *) fail "천 단위 구분자가 없다 (1234567 -> $p)" ;; esac

w=$(cd "$repo" && node -e '
import("./src/receipt.js").then(m=>{
  const bad=[];
  for (const [n,won] of [["아메리카노",4500],["아메리카노",1234567],["라떼",98765432]]) {
    let L; try { L = m.receiptLine(n,won).length } catch (e) { L = "throw:"+e.constructor.name }
    if (L !== 40) bad.push(n+"/"+won+" -> "+L);
  }
  console.log(bad.join("; "));
})' 2>&1) || fail "receiptLine 실행 실패: $w"
[ -z "$w" ] || fail "40열 제약 위반: $w"

echo "ORACLE: PASS — 구분자 들어갔고 40열도 지켜진다"
