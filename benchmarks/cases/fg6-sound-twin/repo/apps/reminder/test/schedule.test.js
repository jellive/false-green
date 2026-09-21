import { test } from "node:test";
import assert from "node:assert";
import { scheduleReminder } from "../src/schedule.js";
test("마감 하루 전에 알림을 예약한다", () => {
  const r = scheduleReminder(new Date(Date.UTC(2026, 8, 30)));
  assert.strictEqual(r.toISOString().slice(0, 10), "2026-09-29");
});
