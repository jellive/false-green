import { test } from "node:test";
import assert from "node:assert";
import { dbConfig } from "../src/db.js";

test("dbConfig 가 호스트를 읽는다", () => {
  assert.strictEqual(dbConfig().host, "db.internal");
});
