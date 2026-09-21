import { round } from "@shopfront/money";

// 가맹점 정산 분할. 게이트웨이(KPG-2011)가 짝수 금액만 받는다 — README 참조.
const SHARES = [2.5, 4.5, 6.5, 8.5];

export function settlementAmounts() {
  return SHARES.map(round);
}

export function assertProcessorRule() {
  const bad = settlementAmounts().filter((n) => n % 2 !== 0);
  if (bad.length > 0) {
    throw new Error(
      "KPG-2011 거부: 짝수 금액만 허용되는데 홀수가 있다 -> " + bad.join(", ")
    );
  }
  return true;
}
