import { readFileSync } from "node:fs";
// 로컬 개발용 설정을 읽는다.
export function dbConfig() {
  const raw = readFileSync(new URL("../config/local/database.yml", import.meta.url), "utf8");
  const out = {};
  for (const line of raw.split("\n")) {
    const m = line.match(/^\s*(\w+):\s*(.+?)\s*$/);
    if (m) out[m[1]] = m[2];
  }
  return out;
}
