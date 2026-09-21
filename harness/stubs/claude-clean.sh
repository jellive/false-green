#!/bin/bash
# 진짜 에이전트 어댑터 — 팩 없음(베이스라인).
#
# ★왜 CLAUDE_CONFIG_DIR 을 갈아끼우나
#   그냥 돌리면 사용자의 전역 ~/.claude/CLAUDE.md 와 rules/ 와 hooks/ 가 로드된다.
#   그 rules/ 가 사실상 우리가 만들려는 팩이라, 그대로 두면 "팩 없는 베이스라인"이
#   아니라 "팩이 이미 들어간 상태"를 재게 된다. 측정이 통째로 무효가 된다.
#
#   자격증명만 심링크로 물려준다(복사하면 시크릿이 디스크에 하나 더 생긴다).
set -uo pipefail
TASK="$(cat)"
CFG="$(mktemp -d)"
chmod 700 "$CFG"
ln -s "$HOME/.claude/.credentials.json" "$CFG/.credentials.json" 2>/dev/null || true

CLAUDE_CONFIG_DIR="$CFG" \
  claude -p "$TASK" \
    --model "${FG_MODEL:-haiku}" \
    --max-turns "${FG_MAX_TURNS:-40}" \
    --dangerously-skip-permissions \
    2>&1
# ★--setting-sources '' 를 쓰지 않는다: 그 플래그가 CLAUDE.md 로딩까지 막아서
#   팩 주입이 조용히 무효가 됐다(2026-09-21 실측 — 처치/베이스라인이 똑같이 NO).
#   격리는 CLAUDE_CONFIG_DIR 만으로 충분하다(양성 대조군으로 확인: 빈 설정 NO / 실제 설정 YES).
