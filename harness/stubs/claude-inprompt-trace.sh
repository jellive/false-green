#!/bin/bash
# (진단용) 팩을 CLAUDE.md 가 아니라 과제 프롬프트 앞에 붙인다. 바뀌는 변수는 "자리" 하나다.
#   haiku 가 CLAUDE.md 로 받은 팩은 무시했다(6/6). 프롬프트로 받으면 달라지나?
#   달라지면: 팩 내용은 쓸 만하고 전달 경로가 문제 → 배포 형태를 바꿔야 한다
#   안 달라지면: 모델이 이 원칙을 작업 중에 적용하지 못한다 → 팩으로 해결 안 되는 층
set -uo pipefail
TASK="$(cat)"
PACK="${FG_PACK:?}"
CFG="$(mktemp -d)"; chmod 700 "$CFG"
ln -s "$HOME/.claude/.credentials.json" "$CFG/.credentials.json" 2>/dev/null || true
PROMPT="$(cat "$PACK")

---

$TASK"
CLAUDE_CONFIG_DIR="$CFG" \
  claude -p "$PROMPT" \
    --model "${FG_MODEL:-haiku}" \
    --max-turns "${FG_MAX_TURNS:-40}" \
    --dangerously-skip-permissions \
    --output-format stream-json --verbose \
    2>&1
