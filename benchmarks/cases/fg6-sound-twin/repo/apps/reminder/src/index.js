import { scheduleReminder } from "./schedule.js";
console.log("알림 시각:", scheduleReminder(new Date(Date.UTC(2026, 8, 30))).toISOString());
