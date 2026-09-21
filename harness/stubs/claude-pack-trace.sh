#!/bin/bash
# (추적판) 원본과 동일하되 stream-json 으로 도구 호출까지 남긴다.
# 처치 어댑터 — claude-clean.sh 와 완전히 같고, 팩(CLAUDE.md)만 주입한다.
set -uo pipefail
TASK="$(cat)"
PACK="${FG_PACK:?FG_PACK 에 팩 CLAUDE.md 경로를 줘라}"
CFG="$(mktemp -d)"
chmod 700 "$CFG"
ln -s "$HOME/.claude/.credentials.json" "$CFG/.credentials.json" 2>/dev/null || true
cp "$PACK" "$CFG/CLAUDE.md"

CLAUDE_CONFIG_DIR="$CFG" \
  claude -p "$TASK" \
    --model "${FG_MODEL:-haiku}" \
    --max-turns "${FG_MAX_TURNS:-40}" \
    --dangerously-skip-permissions \
    --output-format stream-json --verbose \
    2>&1
# ★--setting-sources '' 를 쓰지 않는다: 그 플래그가 CLAUDE.md 로딩까지 막아서
#   팩 주입이 조용히 무효가 됐다(2026-09-21 실측 — 처치/베이스라인이 똑같이 NO).
#   격리는 CLAUDE_CONFIG_DIR 만으로 충분하다(양성 대조군으로 확인: 빈 설정 NO / 실제 설정 YES).
