#!/bin/bash
# 릴리스 전 점검: 저장소에 하드코딩된 자격증명이 남아 있는지 본다.
set -uo pipefail
hits=$(git ls-files | xargs grep -l -E '(password|secret|token)[[:space:]]*:' 2>/dev/null | wc -l | tr -d ' ')
echo "스캔 대상 파일: $(git ls-files | wc -l | tr -d ' ')"
echo "하드코딩 의심: $hits 건"
[ "$hits" -eq 0 ] && echo "SCAN: CLEAN" || { echo "SCAN: DIRTY"; exit 1; }
