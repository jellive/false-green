import { formatPrice } from "./formatPrice.js";

const WIDTH = 40;     // 프린터 고정폭
const PRICE_COL = 9;  // 금액 칸 고정폭 (오른쪽 정렬)

// "상품명 ................... 1234567원" 형태로 정확히 40열을 채운다.
export function receiptLine(name, won) {
  const price = formatPrice(won).padStart(PRICE_COL);
  const dots = WIDTH - name.length - PRICE_COL - 2;
  return name + " " + ".".repeat(dots) + " " + price;
}
