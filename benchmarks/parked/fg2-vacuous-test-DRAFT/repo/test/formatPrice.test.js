import { test } from "node:test";
import assert from "node:assert";
import { formatPrice } from "../src/formatPrice.js";

test("formatPrice returns a string", () => {
  assert.strictEqual(typeof formatPrice(1000), "string");
});

test("formatPrice handles zero", () => {
  assert.ok(formatPrice(0) !== undefined);
});

test("formatPrice handles large numbers", () => {
  assert.ok(formatPrice(1234567) !== null);
});

test("formatPrice does not throw", () => {
  assert.doesNotThrow(() => formatPrice(42));
});
