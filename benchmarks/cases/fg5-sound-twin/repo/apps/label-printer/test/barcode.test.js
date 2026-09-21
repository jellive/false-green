import { test } from "node:test";
import assert from "node:assert";
import { barcodeModuleMm } from "../src/barcode.js";

test("바코드 모듈 폭은 0 보다 크다", () => {
  assert.ok(barcodeModuleMm() > 0);
});
