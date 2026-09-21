import { round } from "@shopfront/money";
export function withTax(amount, rate) {
  return round(amount * (1 + rate));
}
