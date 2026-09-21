import { test } from "node:test";
import assert from "node:assert";
import { formatPrice } from "../src/formatPrice.js";

test("formatPrice 는 원 단위를 붙인다", () => {
  assert.ok(formatPrice(1000).endsWith("원"));
});
test("formatPrice 는 숫자를 보존한다", () => {
  assert.ok(formatPrice(4500).replace(/[^0-9]/g, "") === "4500");
});
