import { test } from "node:test";
import assert from "node:assert";
import { assertProcessorRule, settlementAmounts } from "../src/settlement.js";

test("정산 금액은 게이트웨이 제약(짝수)을 지킨다", () => {
  assert.strictEqual(assertProcessorRule(), true);
});

test("정산 금액이 4건 나온다", () => {
  assert.strictEqual(settlementAmounts().length, 4);
});
