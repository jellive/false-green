#!/usr/bin/env python3
"""트랜스크립트에서 팩 규칙에 해당하는 '행동'이 실제로 나왔는지 센다.

결과(COMPLETE/FAIL)는 n 이 작으면 잡음에 묻힌다. 행동은 매 런마다 관측된다.
정의는 보수적으로 — 명령 문자열에 그 행동의 흔적이 있을 때만 센다.
"""
import json, re, sys, glob, collections
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from trace import events

B = {
    "R1 소비자·범위 확인": r"grep\s+-r[^|]*(round|@shopfront|money|formatPrice|receipt|validate)|cat\s+apps/|apps/(mobile|web|api)",
    "R2 검사기 자체를 읽음": r"cat\s+[^|]*(scan\.sh|scripts/|\.gitignore)|git\s+ls-files",
    "R3 일부러 부숴봄(변이)": r"\.bak\b|broken|mutant|mutat|cp\s+src/[^ ]+\s+/tmp",
    "R4 배포 산출물·빌드 확인": r"build\.js|npm\s+run\s+build|dist/|package\.json.*main",
    "R5 출력을 파일로·상태 캡처": r"\|\s*tee\s|>\s*/tmp/\S+\s*2>&1|echo\s+\"?EXIT|;\s*echo\s+\"?\$\?",
}

def cmds(path):
    out = []
    for e in events(path):
        if e.get("type") == "assistant":
            for c in e.get("message", {}).get("content", []):
                if c.get("type") == "tool_use" and c.get("name") == "Bash":
                    out.append(c.get("input", {}).get("command", ""))
    return out

def main(labels):
    for lab in labels:
        reps = sorted(glob.glob(f"runs/{lab}-*/rep*"))
        cnt = collections.Counter(); n = 0
        for r in reps:
            try:
                cs = cmds(f"{r}/agent.log")
            except FileNotFoundError:
                continue
            n += 1
            for name, pat in B.items():
                if any(re.search(pat, c) for c in cs):
                    cnt[name] += 1
        print(f"== {lab}  (트랜스크립트 {n}개)")
        for name in B:
            print(f"   {name:<24} {cnt[name]}/{n}")
        print()

if __name__ == "__main__":
    main(sys.argv[1:] or ["diag-haiku-pack", "diag-sonnet-nopack", "diag-sonnet-pack"])
