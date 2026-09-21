import { round } from "@shopfront/money";
export function cartTotal(items) {
  return round(items.reduce((s, i) => s + i.price, 0));
}
