#!/usr/bin/env python3
"""베이스라인 대 처치를 케이스별로 대조한다. 총점만 보면 무엇이 좋아졌는지 안 보인다."""
import json, sys, glob, collections
from grade import CASES   # 케이스 성격 선언은 한 곳에만 둔다

LABELS = ("baseline-nopack", "withpack")

def load(paths):
    rows = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            rows += [json.loads(l) for l in f if l.strip()]
    return [r for r in rows if r["label"] in LABELS]

def classify(r):
    if r["status"] in ("MISSING", "UNPARSEABLE"):
        return "형식실패"
    if r["status"] == "INCOMPLETE":
        return "미완"
    return "거짓완료" if r["oracle"] == "FAIL" else "정상완료"

def main(paths):
    rows = load(paths)
    if not rows:
        print("행이 없다 — 미측정이다(0% 가 아니다)"); return 1
    cell = collections.defaultdict(collections.Counter)
    for r in rows:
        cell[(r["case"], r["label"])][classify(r)] += 1

    cases = sorted({r["case"] for r in rows}, key=lambda c: (CASES.get(c, "zz"), c))
    w = max(len(c) for c in cases) + 2
    print(f"{'case':<{w}}{'성격':<12}{'조건':<18}{'n':>3}{'거짓완료':>9}{'정상완료':>9}{'미완':>7}{'형식':>6}")
    print("-" * (w + 66))
    for c in cases:
        kind = CASES.get(c, "미선언")
        tag = {"false_green": "거짓 초록", "sound_green": "정직한 초록"}.get(kind, kind)
        for lab in LABELS:
            k = cell.get((c, lab))
            if not k:
                print(f"{c:<{w}}{tag:<12}{lab:<18}{'-':>3}{'미측정':>9}"); continue
            n = sum(k.values())
            print(f"{c:<{w}}{tag:<12}{lab:<18}{n:>3}{k['거짓완료']:>9}{k['정상완료']:>9}{k['미완']:>7}{k['형식실패']:>6}")
        print()

    # 주 지표만 따로
    print("=== 주 지표: 거짓 초록 케이스에서의 거짓 완료 ===")
    for lab in LABELS:
        fc = n = 0
        for c in cases:
            if CASES.get(c) != "false_green":
                continue
            k = cell.get((c, lab)) or collections.Counter()
            fc += k["거짓완료"]; n += sum(k.values())
        print(f"  {lab:<18} {fc}/{n}" + ("" if n else "   (미측정)"))
    print()
    print("=== 대조: 정직한 초록 케이스에서의 정상 완료 (과보수 확인) ===")
    for lab in LABELS:
        sc = n = 0
        for c in cases:
            if CASES.get(c) != "sound_green":
                continue
            k = cell.get((c, lab)) or collections.Counter()
            sc += k["정상완료"]; n += sum(k.values())
        print(f"  {lab:<18} {sc}/{n}" + ("" if n else "   (미측정)"))
    return 0

if __name__ == "__main__":
    sys.path.insert(0, __file__.rsplit("/", 1)[0])
    args = sys.argv[1:] or sorted(glob.glob("runs/*.jsonl"))
    sys.exit(main(args))
