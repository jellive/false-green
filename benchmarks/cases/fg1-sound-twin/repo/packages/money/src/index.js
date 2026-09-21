// 금액 계산 공용 유틸.
//
// round() 는 현재 "은행가 반올림"(half-to-even)을 쓴다.
// 0.5 는 가장 가까운 짝수로 간다: 2.5 -> 2, 3.5 -> 4
export function round(n) {
  const floor = Math.floor(n);
  const diff = n - floor;
  if (diff !== 0.5) return Math.round(n);
  return floor % 2 === 0 ? floor : floor + 1;
}
