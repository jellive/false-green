#!/bin/bash
# 백업 아카이브에 hooks/ 가 들어 있는지 확인한다.
set -euo pipefail

if tar -tzf backup.tar.gz | grep -q 'hooks/'; then
  echo "OK: 백업에 hooks 포함됨"
else
  echo "FAIL: 메타에 hooks 없음"
  exit 1
fi
