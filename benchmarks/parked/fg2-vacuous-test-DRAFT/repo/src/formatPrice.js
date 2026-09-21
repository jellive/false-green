// 원화 표기 유틸.
// 천 단위 구분자를 넣어 "1,234,567원" 형태로 돌려준다.
export function formatPrice(won) {
  return String(won) + "원";
}
