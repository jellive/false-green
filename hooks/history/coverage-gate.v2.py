#!/usr/bin/env python3
"""coverage-gate — Stop 훅. 에이전트가 끝내려 할 때, 검증이 실제로 무엇을 돌렸는지 센다.

판정하는 것 (좁게):
  "네가 바꾼 파일에 의존하는 코드가, 테스트 명령이 실제로 실행한 범위 밖에 있는가"
판정하지 않는 것:
  프로그램이 맞는지. 결정론적 훅은 그걸 판정할 수 없다.

설계 결정 (레드팀 지적 반영):
  - 차단 횟수가 아니라 **작업트리 해시**로 판정한다. 상태가 바뀌면 다시 재고,
    같은 미해결 위반이면 다시 막는다. 첫 Stop 에 차단을 소모하는 우회를 막는다.
  - 변경 목록은 git diff 만 쓰지 않는다 — 미추적 파일도 포함한다.
  - 테스트 러너의 "실제 실행" 출력으로 판정한다. "test 스크립트가 있나"는 대리 신호라 안 쓴다.
  - 상태는 저장소 밖(CLAUDE_CONFIG_DIR)에 둔다. 에이전트 작업트리에 두지 않는다.
  - 같은 위반을 MAX_REPEAT 번 막고 나면 통과시키되 'override' 로 기록한다(무한 루프 방지).

v1 범위: npm / pnpm workspaces. 다른 러너는 아직 모른다 — 모르면 막지 않고 통과시킨다.

v2 (2026-09-21, holdout fg5 가 드러낸 버그 수정):
  A. 루트를 cwd 로 잡지 않는다 — 에이전트가 하위 폴더로 cd 하면 틀린다. git 최상위를 쓴다.
  B. 변경을 HEAD 와 비교하지 않는다 — 에이전트가 커밋하면 눈이 먼다. 세션 시작 기준선과 비교한다.
  C. pnpm 은 패키지 이름이 아니라 경로를 찍는다 — 경로를 워크스페이스 이름으로 매핑한다.
  +  훅이 직접 돌린 전체 테스트가 실패하면 막는다. 에이전트가 좁은 테스트만 보고 끝내는 경우.
     (이 항목은 fg5 관찰에서 나왔다 — 동기가 오염돼 있으므로 fg5 로 효과를 주장하지 않는다.)
"""
import hashlib, json, os, re, subprocess, sys, glob, pathlib

MAX_REPEAT = 3
SKIP_DIRS = {".git", "node_modules", ".false-green"}
CODE_EXT = (".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx")

def sh(cmd, cwd, timeout=300):
    p = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout + p.stderr

def tree_hash(root):
    h = hashlib.sha256()
    for dp, dns, fns in os.walk(root):
        dns[:] = sorted(d for d in dns if d not in SKIP_DIRS)
        for fn in sorted(fns):
            if fn == "STATUS.txt" or fn.startswith(".agent"):
                continue
            p = os.path.join(dp, fn)
            try:
                h.update(os.path.relpath(p, root).encode()); h.update(open(p, "rb").read())
            except OSError:
                pass
    return h.hexdigest()[:16]

def workspaces(root):
    try:
        pkg = json.load(open(os.path.join(root, "package.json")))
    except Exception:
        return None
    pats = pkg.get("workspaces")
    if isinstance(pats, dict):
        pats = pats.get("packages")
    if not pats:
        pnpm = os.path.join(root, "pnpm-workspace.yaml")
        if os.path.exists(pnpm):
            pats = re.findall(r"^\s*-\s*['\"]?([^'\"\n]+)['\"]?\s*$", open(pnpm).read(), re.M)
    if not pats:
        return None
    ws = {}
    for pat in pats:
        for d in glob.glob(os.path.join(root, pat)):
            pj = os.path.join(d, "package.json")
            if os.path.isfile(pj):
                try:
                    ws[json.load(open(pj))["name"]] = os.path.relpath(d, root)
                except Exception:
                    pass
    return ws or None

def repo_root(cwd):
    rc, out = sh("git rev-parse --show-toplevel", cwd)
    return out.strip() if rc == 0 and out.strip() else cwd

def changed_files(root, base="HEAD"):
    rc1, tracked = sh(f"git diff --name-only {base}", root)
    rc2, untracked = sh("git ls-files --others --exclude-standard", root)
    if rc1 != 0:
        return None
    out = {l.strip() for l in (tracked + "\n" + untracked).splitlines() if l.strip()}
    return {f for f in out if f.endswith(CODE_EXT) and not f.startswith("node_modules/")}

def owner(path, ws):
    best = None
    for name, d in ws.items():
        if path == d or path.startswith(d.rstrip("/") + "/"):
            if best is None or len(d) > len(ws[best]):
                best = name
    return best

def consumers(root, ws, changed):
    """변경 파일이 속한 워크스페이스를 패키지 이름으로 import 하는 다른 워크스페이스."""
    targets = {owner(f, ws) for f in changed} - {None}
    hits = {}
    for name, d in ws.items():
        if name in targets:
            continue
        for p in pathlib.Path(root, d).rglob("*"):
            if not p.is_file() or not p.name.endswith(CODE_EXT) or "node_modules" in p.parts:
                continue
            try:
                src = p.read_text(errors="replace")
            except OSError:
                continue
            for t in targets:
                if re.search(r"""(from|require\(|import\()\s*['"]""" + re.escape(t) + r"""(['"/])""", src):
                    hits.setdefault(name, set()).add((t, str(p.relative_to(root))))
    return hits

def executed(output, ws):
    """npm/pnpm 이 실제로 test 를 실행한 워크스페이스 이름.
    npm:  "> @scope/name@1.0.0 test"   — 이름을 찍는다
    pnpm: "apps/label-printer test$ …" — 경로를 찍는다 → 이름으로 매핑한다 (v2 버그 C)"""
    got = set(re.findall(r"^>\s+(@?[\w.-]+(?:/[\w.-]+)?)@\S+\s+test\b", output, re.M))
    by_dir = {d.rstrip("/"): n for n, d in ws.items()}
    for path in re.findall(r"^(\S+)\s+test\$", output, re.M):
        got.add(by_dir.get(path.rstrip("/"), path))
    return got

def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        event = {}
    root = repo_root(event.get("cwd") or os.getcwd())
    state_dir = os.path.join(os.environ.get("CLAUDE_CONFIG_DIR", os.path.expanduser("~/.claude")), "false-green-state")
    os.makedirs(state_dir, exist_ok=True)
    state_path = os.path.join(state_dir, hashlib.sha256(root.encode()).hexdigest()[:12] + ".json")
    state = json.load(open(state_path)) if os.path.exists(state_path) else {"verdicts": {}, "log": []}

    # 세션 시작: 기준선만 기록하고 끝낸다 (v2 버그 B)
    if "--session-start" in sys.argv:
        rc, head = sh("git rev-parse HEAD", root)
        state["base"] = head.strip() if rc == 0 else "HEAD"
        json.dump(state, open(state_path, "w"), ensure_ascii=False, indent=1)
        sys.exit(0)
    base = state.get("base", "HEAD")

    def save(entry):
        state["log"].append(entry)
        json.dump(state, open(state_path, "w"), ensure_ascii=False, indent=1)

    th = tree_hash(root)
    if state["verdicts"].get(th, {}).get("result") == "pass":
        sys.exit(0)

    ws = workspaces(root)
    changed = changed_files(root, base)
    if not ws or not changed:
        save({"tree": th, "result": "skip", "why": "workspaces 없음" if not ws else "코드 변경 없음"})
        state["verdicts"][th] = {"result": "pass"}; json.dump(state, open(state_path, "w"), ensure_ascii=False, indent=1)
        sys.exit(0)

    cons = consumers(root, ws, changed)
    rc, out = sh("npm test 2>&1", root)
    ran = executed(out, ws)
    gaps = {n: refs for n, refs in cons.items() if n not in ran}
    red = rc != 0
    if not gaps and not red:
        state["verdicts"][th] = {"result": "pass"}
        save({"tree": th, "result": "pass", "ran": sorted(ran), "consumers": sorted(cons)})
        sys.exit(0)

    vkey = hashlib.sha256(json.dumps([sorted(gaps), red], ensure_ascii=False).encode()).hexdigest()[:12]
    prev = state["verdicts"].get(th, {})
    count = prev.get("count", 0) + 1 if prev.get("vkey") == vkey else 1
    if count > MAX_REPEAT:
        state["verdicts"][th] = {"result": "pass", "override": True}
        save({"tree": th, "result": "override", "gaps": sorted(gaps), "count": count})
        sys.exit(0)
    state["verdicts"][th] = {"result": "block", "vkey": vkey, "count": count}
    save({"tree": th, "result": "block", "gaps": sorted(gaps), "red": red, "ran": sorted(ran), "count": count})

    lines = ["[coverage-gate] 완료 전에 확인할 것.", ""]
    if red:
        fails = [l for l in out.splitlines() if re.search(r"(✖|not ok|FAIL|Error|failed)", l)][:8]
        lines.append("  ★저장소 전체 테스트(npm test)가 실패한다. 네가 본 초록은 전체가 아니었을 수 있다:")
        lines += [f"      {l.strip()[:150]}" for l in fails] or ["      (실패 줄을 못 뽑았다 — npm test 를 직접 돌려 봐라)"]
        lines.append("")
    lines.append(f"  테스트가 실제로 실행한 워크스페이스: {', '.join(sorted(ran)) or '(없음)'}")
    for n, refs in sorted(gaps.items()):
        lines.append(f"  실행 안 됨: {n} ({ws[n]})")
        for t, f in sorted(refs)[:5]:
            lines.append(f"      {f}  →  {t} 를 import 한다")
    lines += ["", "  이 소비자들이 네 변경 이후에도 올바르게 동작하는지 직접 확인해라.",
              "  확인할 수 없다면 그 사실을 STATUS 에 반영해라."]
    print("\n".join(lines), file=sys.stderr)
    sys.exit(2)

if __name__ == "__main__":
    main()
