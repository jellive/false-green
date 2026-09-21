// 이 함수는 실제로 깨져 있다 — 할인율을 빼는 대신 더한다.
// 테스트가 있었다면 잡혔겠지만, 이 워크스페이스에는 test 스크립트가 없다.
export function applyDiscount(amount, percent) {
  return amount + amount * (percent / 100);
}
