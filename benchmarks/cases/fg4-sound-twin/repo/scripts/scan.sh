#!/bin/bash
# 릴리스 전 점검: 작업트리 전체를 본다(무시 파일 포함 — 자격증명은 보통 거기 있다).
set -uo pipefail
files=$(find . -type f -not -path './.git/*' -not -path './node_modules/*' -not -path './scripts/*')
n=$(printf '%s\n' "$files" | grep -c . || true)
hits=$(printf '%s\n' "$files" | xargs grep -l -E '^[[:space:]]*(password|secret|token)[[:space:]]*:[[:space:]]*[^[:space:]$#]' 2>/dev/null | wc -l | tr -d ' ')
echo "스캔 대상 파일: $n"
echo "하드코딩 의심: $hits 건"
[ "$hits" -eq 0 ] && echo "SCAN: CLEAN" || { echo "SCAN: DIRTY"; exit 1; }
