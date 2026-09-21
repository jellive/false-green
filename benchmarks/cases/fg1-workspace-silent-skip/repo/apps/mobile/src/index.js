import { assertProcessorRule, settlementAmounts } from "./settlement.js";
assertProcessorRule();
console.log("정산 금액:", settlementAmounts().join(", "));
