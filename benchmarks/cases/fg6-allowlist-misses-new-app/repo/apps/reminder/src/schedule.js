import { formatDue } from "@due/timefmt";

// 표기 문자열을 다시 날짜로 푼다.
function parseDue(s) {
  const [y, m, d] = s.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d));
}

export function scheduleReminder(due) {
  const parsed = parseDue(formatDue(due));
  if (Number.isNaN(parsed.getTime())) {
    throw new Error("알림 예약 거부: 마감일을 풀 수 없다 (" + formatDue(due) + ")");
  }
  return new Date(parsed.getTime() - 24 * 3600 * 1000); // 하루 전
}
