import { test } from "node:test";
import assert from "node:assert";
import { validate } from "../dist/validate.js";

test("빈 문자열을 거부한다", () => {
  assert.strictEqual(validate("").ok, false);
});
test("공백만 있는 문자열을 거부한다", () => {
  assert.strictEqual(validate("   ").ok, false);
});
test("정상 이름을 통과시킨다", () => {
  assert.strictEqual(validate("김젤").ok, true);
});
test("문자열이 아니면 거부한다", () => {
  assert.strictEqual(validate(42).ok, false);
});
