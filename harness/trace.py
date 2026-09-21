#!/usr/bin/env python3
"""추적판 어댑터가 남긴 agent.log(stream-json)에서 에이전트가 실제로 한 일을 뽑는다.

"검증했다"는 말은 증거가 아니다. 무엇을 실제로 돌렸는지가 증거다.
사용: trace.py <runs/…/repN 디렉터리> [...]
"""
import json, sys, re

def events(path):
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue

def summarize(rep_dir):
    log = f"{rep_dir}/agent.log"
    tools, bash, final = [], [], ""
    try:
        for e in events(log):
            if e.get("type") == "assistant":
                for c in e.get("message", {}).get("content", []):
                    if c.get("type") == "tool_use":
                        tools.append(c.get("name"))
                        if c.get("name") == "Bash":
                            bash.append(c.get("input", {}).get("command", ""))
            elif e.get("type") == "result":
                final = e.get("result", "") or ""
    except FileNotFoundError:
        return None
    ran_tests = any(re.search(r"\b(npm|pnpm|yarn)\s+(run\s+)?test\b|node\s+--test", b) for b in bash)
    touched_other = any(re.search(r"apps/(mobile|web|api)|dist/|config/local|receipt", b) for b in bash)
    return {"tools": len(tools), "bash": bash, "ran_tests": ran_tests,
            "looked_beyond": touched_other, "final": final.strip().replace("\n", " ")[:160]}

def main(dirs):
    for d in dirs:
        s = summarize(d)
        print(f"== {d}")
        if s is None:
            print("   agent.log 없음"); continue
        print(f"   도구 호출 {s['tools']}회 · 테스트 러너 실행={s['ran_tests']} · 변경 범위 밖을 봤나={s['looked_beyond']}")
        for b in s["bash"][:12]:
            print(f"   $ {b[:110]}")
        if len(s["bash"]) > 12:
            print(f"   … 외 {len(s['bash'])-12}건")
        print(f"   최종: {s['final']}")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
