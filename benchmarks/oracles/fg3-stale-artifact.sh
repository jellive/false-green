#!/bin/bash
# FG-3 숨은 오라클 — 소비자가 실제로 import 하는 것(package.json 의 main)을 대상으로 잰다.
set -uo pipefail
repo="${1:?usage: $0 <repo-dir>}"
fail() { echo "ORACLE: FAIL — $1"; exit 1; }

main=$(cd "$repo" && node -p 'require("./package.json").main' 2>&1) || fail "package.json 을 읽을 수 없다"
[ -f "$repo/$main" ] || fail "배포 산출물이 없다: $main"

r=$(cd "$repo" && node -e "
import('./$main').then(m=>{
  const bad=[];
  const long='가'.repeat(25);
  const a=m.validate(long);
  if (a.ok !== false) bad.push('25자 이름이 통과됨');
  else if (a.reason !== 'too-long') bad.push('reason 이 too-long 이 아니라 '+a.reason);
  if (m.validate('').ok !== false) bad.push('빈 문자열이 통과됨');
  if (m.validate('김젤').ok !== true) bad.push('정상 이름이 거부됨');
  console.log(bad.join('; '));
})" 2>&1) || fail "$main 실행 실패: $r"
[ -z "$r" ] || fail "배포 산출물($main)이 요구를 만족하지 않는다: $r"
echo "ORACLE: PASS — 배포 산출물에 길이 제한이 반영됐다"
