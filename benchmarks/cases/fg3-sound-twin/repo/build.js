// src/ 를 dist/ 로 옮긴다(이 프로젝트는 트랜스파일이 없어 복사가 전부다).
import { copyFileSync, mkdirSync } from "node:fs";
mkdirSync("dist", { recursive: true });
copyFileSync("src/validate.js", "dist/validate.js");
console.log("built: dist/validate.js");
