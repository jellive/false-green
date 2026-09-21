import { test } from "node:test";
import assert from "node:assert";
import { formatDue } from "../src/index.js";
test("formatDue 는 문자열을 돌려준다", () => {
  assert.strictEqual(typeof formatDue(new Date(Date.UTC(2026, 0, 5))), "string");
});
test("formatDue 는 연도를 포함한다", () => {
  assert.ok(formatDue(new Date(Date.UTC(2026, 0, 5))).includes("2026"));
});
