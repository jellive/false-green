import { test } from "node:test";
import assert from "node:assert";
import { withTax } from "../src/price.js";

test("withTax applies the rate", () => {
  assert.strictEqual(withTax(1000, 0.1), 1100);
});
