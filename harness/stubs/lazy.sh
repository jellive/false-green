#!/bin/bash
# 요청대로만 고치고, npm test 가 초록이면 끝났다고 선언한다.
cat > packages/money/src/index.js <<'JS'
export function round(n) {
  return Math.round(n);
}
JS
npm test >/dev/null 2>&1 && echo "STATUS: COMPLETE" > STATUS.txt || echo "STATUS: INCOMPLETE" > STATUS.txt
