#!/bin/bash
# 한 케이스를 n회 돌린다. 에이전트는 $FG_AGENT 로 갈아끼운다.
#   FG_AGENT: 실행 파일. cwd=작업트리, stdin=과제문. STATUS.txt 를 남기는 것이 그 책임.
# 사용: FG_AGENT=./harness/stubs/lazy.sh ./harness/run.sh fg1-workspace-silent-skip 3 baseline
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CASE="${1:?usage: run.sh <case-id> <n> <label>}"
N="${2:?}"; LABEL="${3:-unlabeled}"
AGENT="${FG_AGENT:?FG_AGENT 를 지정해라}"

CASEDIR="$ROOT/benchmarks/cases/$CASE"
ORACLE="$ROOT/benchmarks/oracles/$CASE.sh"
[ -d "$CASEDIR/repo" ] || { echo "케이스 없음: $CASEDIR"; exit 2; }
[ -x "$ORACLE" ]       || { echo "오라클 없음: $ORACLE"; exit 2; }

STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$ROOT/runs/$LABEL-$CASE-$STAMP.jsonl"
: > "$OUT"

ART="$ROOT/runs/$LABEL-$CASE-$STAMP"
mkdir -p "$ART"

for i in $(seq 1 "$N"); do
  WD="$(mktemp -d)/repo"
  cp -R "$CASEDIR/repo" "$WD"
  ( cd "$WD" && npm install --silent --no-audit --no-fund ) >/dev/null 2>&1
  # 케이스별 셋업(있으면). 에이전트가 돌기 전에 실행된다.
  [ -x "$CASEDIR/setup.sh" ] && ( cd "$WD" && "$CASEDIR/setup.sh" ) >/dev/null 2>&1
  # 기준선 커밋 — 에이전트 **전에** 찍어야 나중 diff 가 진짜 변경분이 된다.
  # (뒤에 찍으면 전체 트리가 "신규"로 나와 무엇을 고쳤는지 알 수 없다 — 실측)
  ( cd "$WD" && { [ -d .git ] || { git init -q && git add -A \
      && git -c user.name=fixture -c user.email=fixture@local commit -qm "before agent"; }; } ) >/dev/null 2>&1

  ( cd "$WD" && "$AGENT" < "$CASEDIR/TASK.md" ) > "$WD/.agent.log" 2>&1
  agent_rc=$?

  # ── 선언 읽기: 형식 실패를 따로 센다 ──
  if [ ! -f "$WD/STATUS.txt" ]; then
    status="MISSING"
  else
    status=$(grep -m1 -oE 'STATUS:[[:space:]]*(COMPLETE|INCOMPLETE)' "$WD/STATUS.txt" \
             | grep -oE '(COMPLETE|INCOMPLETE)' | head -1)
    [ -n "$status" ] || status="UNPARSEABLE"
  fi

  # ── 숨은 오라클: 에이전트가 나간 뒤, 깨끗한 셸에서 ──
  oracle_out=$("$ORACLE" "$WD" 2>&1); oracle_rc=$?
  oracle=$([ $oracle_rc -eq 0 ] && echo PASS || echo FAIL)

  python3 - "$OUT" "$CASE" "$LABEL" "$i" "$status" "$oracle" "$agent_rc" "$oracle_out" <<'PY'
import json, sys
out, case, label, rep, status, oracle, arc, omsg = sys.argv[1:9]
with open(out, "a", encoding="utf-8") as f:
    f.write(json.dumps({"case":case,"label":label,"rep":int(rep),"status":status,
                        "oracle":oracle,"agent_rc":int(arc),
                        "oracle_msg":omsg.strip()[:200]}, ensure_ascii=False)+"\n")
PY
  # ── 증거 보존: 트랜스크립트와 작업 결과를 남긴다 ──
  #    안 남기면 "왜 그렇게 판단했나"를 사후에 볼 수 없다(임시 디렉터리는 사라진다).
  mkdir -p "$ART/rep$i"
  cp "$WD/.agent.log" "$ART/rep$i/agent.log" 2>/dev/null || true
  cp "$WD/STATUS.txt" "$ART/rep$i/STATUS.txt" 2>/dev/null || true
  cp "$WD/.agent.gate.json" "$ART/rep$i/gate.json" 2>/dev/null || true
  ( cd "$WD" && git add -A 2>/dev/null; git diff --cached --stat > "$ART/rep$i/changed.txt" 2>/dev/null ) || true
  printf "%s\n" "$oracle_out" > "$ART/rep$i/oracle.txt"

  printf "[%s rep %s] STATUS=%-11s ORACLE=%s\n" "$CASE" "$i" "$status" "$oracle"
done
echo "→ $OUT"
