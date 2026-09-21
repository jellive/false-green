import { test } from "node:test";
import assert from "node:assert";
import { isOverdue } from "../src/index.js";
test("지난 날짜는 연체", () => {
  assert.strictEqual(isOverdue(new Date(0), new Date(1000)), true);
});
