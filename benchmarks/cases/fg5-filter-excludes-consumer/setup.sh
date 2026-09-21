#!/bin/bash
# pnpm 워크스페이스라 pnpm 으로 링크한다(workspace:* 는 네트워크 불필요).
set -e
pnpm install --offline --silent >/dev/null 2>&1 || pnpm install --silent >/dev/null 2>&1
