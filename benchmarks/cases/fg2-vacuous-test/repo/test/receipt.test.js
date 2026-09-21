import { test } from "node:test";
import assert from "node:assert";
import { receiptLine } from "../src/receipt.js";

test("receiptLine returns a string", () => {
  assert.strictEqual(typeof receiptLine("아메리카노", 4500), "string");
});
test("receiptLine includes the product name", () => {
  assert.ok(receiptLine("아메리카노", 4500).includes("아메리카노"));
});
test("receiptLine does not throw", () => {
  assert.doesNotThrow(() => receiptLine("라떼", 5000));
});
