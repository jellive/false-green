import { mmFromInch } from "@acme/units";

const MODULE_INCH = 0.013;

export function barcodeModuleMm() {
  const mm = mmFromInch(MODULE_INCH);
  if (!(mm > 0)) {
    throw new Error("바코드 모듈 폭이 0 이다 — 스캐너가 읽을 수 없다 (mm=" + mm + ")");
  }
  return mm;
}
