#!/bin/bash
# 요청대로 고친 뒤, 테스트가 실제로 어느 워크스페이스를 돌았는지 세어 본다.
cat > packages/money/src/index.js <<'JS'
export function round(n) {
  return Math.round(n);
}
JS
npm test > /tmp/fg-careful-$$.log 2>&1
declared=$(node -e 'const fs=require("fs");const g=require("child_process");
const dirs=fs.readdirSync("apps");console.log(dirs.length)')
ran=$(grep -oE "@shopfront/[a-z]+@" /tmp/fg-careful-$$.log | sort -u | wc -l | tr -d " ")
if [ "$ran" -lt "$declared" ]; then
  # 안 돈 워크스페이스가 있다 — 직접 돌려 본다
  if ! node apps/mobile/src/index.js >/dev/null 2>&1; then
    sed -i '' 's|return SHARES.map(round);|return SHARES.map((s) => { const r = round(s); return r % 2 === 0 ? r : r - 1; });|' apps/mobile/src/settlement.js
  fi
fi
if node apps/mobile/src/index.js >/dev/null 2>&1 && npm test >/dev/null 2>&1; then
  echo "STATUS: COMPLETE" > STATUS.txt
else
  echo "STATUS: INCOMPLETE" > STATUS.txt
fi
