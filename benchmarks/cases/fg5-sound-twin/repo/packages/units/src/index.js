// 인치 → 밀리미터. 소수점 둘째 자리까지 반올림한다.
export function mmFromInch(inch) {
  return Math.round(inch * 25.4 * 100) / 100;
}
