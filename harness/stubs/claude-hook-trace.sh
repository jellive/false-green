#!/bin/bash
# 처치 어댑터 — 격리 설정 + coverage-gate Stop 훅. 팩(CLAUDE.md)은 넣지 않는다.
# 베이스라인(claude-clean-trace.sh)과 다른 것은 settings.json 의 Stop 훅 하나뿐이다.
set -uo pipefail
TASK="$(cat)"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CFG="$(mktemp -d)"; chmod 700 "$CFG"
ln -s "$HOME/.claude/.credentials.json" "$CFG/.credentials.json" 2>/dev/null || true
cat > "$CFG/settings.json" <<JSON
{ "hooks": {
    "SessionStart": [ { "hooks": [ { "type": "command", "command": "python3 $ROOT/hooks/coverage-gate.py --session-start" } ] } ],
    "Stop":         [ { "hooks": [ { "type": "command", "command": "python3 $ROOT/hooks/coverage-gate.py" } ] } ] } }
JSON
CLAUDE_CONFIG_DIR="$CFG" \
  claude -p "$TASK" \
    --model "${FG_MODEL:-haiku}" \
    --max-turns "${FG_MAX_TURNS:-40}" \
    --dangerously-skip-permissions \
    --output-format stream-json --verbose \
    2>&1
# 훅 판정 기록을 작업트리 밖에서 가져와 증거로 남긴다
f=$(ls "$CFG"/false-green-state/*.json 2>/dev/null | head -1); [ -n "$f" ] && cp "$f" "$PWD/.agent.gate.json" || true
