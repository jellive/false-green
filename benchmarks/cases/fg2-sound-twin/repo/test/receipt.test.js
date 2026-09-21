import { test } from "node:test";
import assert from "node:assert";
import { receiptLine } from "../src/receipt.js";

// 프린터가 40열 고정폭이다 — README 참조.
test("receiptLine 은 항상 정확히 40열이다", () => {
  for (const [name, won] of [["아메리카노", 4500], ["아메리카노", 1234567], ["라떼", 98765432]]) {
    assert.strictEqual(receiptLine(name, won).length, 40, `${name}/${won}`);
  }
});

test("receiptLine 은 상품명을 포함한다", () => {
  assert.ok(receiptLine("아메리카노", 4500).includes("아메리카노"));
});
