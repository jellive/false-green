import { test } from "node:test";
import assert from "node:assert";
import { cartTotal } from "../src/cart.js";

test("cartTotal sums item prices", () => {
  assert.strictEqual(cartTotal([{ price: 1200 }, { price: 3400 }]), 4600);
});
test("cartTotal handles an empty cart", () => {
  assert.strictEqual(cartTotal([]), 0);
});
