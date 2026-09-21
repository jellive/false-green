import { test } from "node:test";
import assert from "node:assert";
import { itemCount } from "../src/cart.js";

test("itemCount counts items", () => {
  assert.strictEqual(itemCount({ items: [1, 2, 3] }), 3);
});
