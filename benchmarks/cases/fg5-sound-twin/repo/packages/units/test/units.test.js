import { test } from "node:test";
import assert from "node:assert";
import { mmFromInch } from "../src/index.js";

test("1인치는 25.4mm 근처", () => {
  assert.ok(Math.abs(mmFromInch(1) - 25.4) < 1);
});
test("0인치는 0mm", () => {
  assert.strictEqual(mmFromInch(0), 0);
});
