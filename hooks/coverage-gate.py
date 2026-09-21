#!/usr/bin/env python3
"""coverage-gate — Stop 훅. 에이전트가 끝내려 할 때, 검증이 실제로 무엇을 돌렸는지 센다.

판정하는 것 (좁게):
  1. 네가 바꾼 파일에 의존하는 워크스페이스가, 테스트 명령이 실제로 실행한 범위 밖에 있는가
  2. 저장소 전체 테스트가 실패하는가 (네가 본 초록이 일부였을 수 있다)
판정하지 않는 것:
  프로그램이 맞는지. 결정론적 훅은 그걸 판정할 수 없다.

★보안 — 이 훅은 저장소의 테스트 명령(`npm test`)을 실행한다. 그게 이 훅의 메커니즘이다.
  에이전트가 `npm test` 를 돌리는 것과 같은 신뢰 경계다. 신뢰하지 않는 저장소에서는 쓰지 마라.
  끄기: COVERAGE_GATE_DISABLE=1

v3 (코드 리뷰 반영): 경로는 -z 로 받는다(비ASCII) · 모르는 러너면 커버리지 판정을 건너뛴다 ·
반복 차단 횟수는 위반 키로 센다(테스트가 파일을 써도 override 에 도달) · 세션 시작 시 더러운
파일을 스냅숏해서 WIP 를 에이전트 탓으로 안 한다 · 상태는 세션별·원자적 쓰기 · 크래시 대신 건너뜀.
"""
import hashlib, json, os, re, subprocess, sys, glob, tempfile

MAX_REPEAT = 3
TEST_TIMEOUT = int(os.environ.get("COVERAGE_GATE_TIMEOUT", "600"))
CODE_EXT = (".js", ".mjs", ".cjs", ".ts", ".mts", ".cts", ".tsx", ".jsx")
READ_CAP = 8 * 1024 * 1024

# ── 실행 ─────────────────────────────────────────────────────────────
def run(args, cwd, timeout=60, shell=False):
    """(rc, stdout, stderr). 시간초과·실행불가면 rc=None. 출력은 깨진 바이트를 대체해서 디코딩한다."""
    try:
        p = subprocess.run(args, cwd=cwd, capture_output=True, timeout=timeout, shell=shell)
        return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return None, "", "timeout"
    except OSError as e:
        return None, "", str(e)

def git_paths(args, root):
    """NUL 구분 경로 목록. 실패하면 None (실패를 '변경 없음'으로 읽지 않는다)."""
    rc, out, _ = run(["git", *args], root)
    if rc != 0:
        return None
    return [p for p in out.split("\0") if p]

def repo_root(cwd):
    rc, out, _ = run(["git", "rev-parse", "--show-toplevel"], cwd)
    return out.strip() if rc == 0 and out.strip() else None

# ── 해시 ─────────────────────────────────────────────────────────────
def blob_hashes(root, paths):
    """경로 → git blob 해시(없는 파일은 None). 링크는 따라가지 않는다."""
    out = {}
    for p in paths:
        full = os.path.join(root, p)
        try:
            st = os.lstat(full)
        except OSError:
            out[p] = None; continue
        if os.path.islink(full):
            data = os.readlink(full).encode()
        elif os.path.isfile(full):
            with open(full, "rb") as f:
                data = f.read(READ_CAP + 1)
        else:
            out[p] = "special"; continue
        out[p] = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
    return out

def base_hashes(root, base, paths):
    out = {}
    for p in paths:
        rc, sha, _ = run(["git", "rev-parse", "-q", "--verify", f"{base}:{p}"], root)
        out[p] = sha.strip() if rc == 0 and sha.strip() else None
    return out

def tree_hash(root):
    """추적 + 무시 안 된 미추적 파일의 (경로, 모드, 내용) — NUL 구분이라 모호하지 않다."""
    files = git_paths(["ls-files", "-z", "-co", "--exclude-standard"], root)
    if files is None:
        return None
    h = hashlib.sha256()
    hashes = blob_hashes(root, sorted(files))
    for p in sorted(files):
        try:
            mode = oct(os.lstat(os.path.join(root, p)).st_mode)
        except OSError:
            mode = "gone"
        h.update(p.encode() + b"\0" + mode.encode() + b"\0" + str(hashes.get(p)).encode() + b"\n")
    return h.hexdigest()[:16]

# ── 워크스페이스 ─────────────────────────────────────────────────────
def _posix(p):
    return p.replace("\\", "/").rstrip("/")

def pnpm_patterns(text):
    """pnpm-workspace.yaml 의 packages 만 읽는다. 블록 목록·인라인 배열·주석·부정(!) 처리."""
    text = re.sub(r"(?m)\s+#.*$", "", text)
    m = re.search(r"(?m)^packages:\s*\[(.*?)\]", text, re.S)
    if m:
        items = [i.strip().strip("'\"") for i in m.group(1).split(",")]
    else:
        m = re.search(r"(?ms)^packages:\s*\n((?:[ \t]+-.*\n?)+)", text)
        items = re.findall(r"-\s*['\"]?([^'\"\n]+?)['\"]?\s*$", m.group(1), re.M) if m else []
    return [i for i in items if i]

def workspaces(root):
    try:
        pkg = json.load(open(os.path.join(root, "package.json"), encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(pkg, dict):
        return None
    pats = pkg.get("workspaces")
    if isinstance(pats, dict):
        pats = pats.get("packages")
    if not pats:
        yml = os.path.join(root, "pnpm-workspace.yaml")
        if os.path.exists(yml):
            try:
                pats = pnpm_patterns(open(yml, encoding="utf-8").read())
            except Exception:
                pats = None
    if not isinstance(pats, list) or not pats:
        return None
    real_root = os.path.realpath(root)
    include = [p for p in pats if isinstance(p, str) and not p.startswith("!")]
    exclude = {_posix(os.path.relpath(os.path.join(root, p[1:]), root)) for p in pats if isinstance(p, str) and p.startswith("!")}
    ws = {}
    for pat in include:
        for d in glob.glob(os.path.join(root, pat)):
            rd = os.path.realpath(d)
            if not (rd == real_root or rd.startswith(real_root + os.sep)):   # 저장소 밖으로 못 나간다
                continue
            rel = _posix(os.path.relpath(d, root))
            if rel in exclude or any(rel.startswith(e + "/") for e in exclude):
                continue
            try:
                name = json.load(open(os.path.join(d, "package.json"), encoding="utf-8")).get("name")
            except Exception:
                continue
            if isinstance(name, str):
                ws[name] = rel
    return ws or None

def owner(path, ws):
    path = _posix(path); best = None
    for name, d in ws.items():
        if path == d or path.startswith(d + "/"):
            if best is None or len(d) > len(ws[best]):
                best = name
    return best

def consumers(root, ws, changed):
    """변경된 워크스페이스를 패키지 이름으로 import 하는 **다른** 워크스페이스.
    변경된 워크스페이스라도 다른 변경 워크스페이스의 소비자면 센다(자기 자신만 뺀다)."""
    targets = {owner(f, ws) for f in changed} - {None}
    hits = {}
    for name, d in ws.items():
        others = targets - {name}
        if not others:
            continue
        for dp, dns, fns in os.walk(os.path.join(root, d)):
            dns[:] = [x for x in dns if x not in ("node_modules", ".git")]
            for fn in fns:
                if not fn.endswith(CODE_EXT):
                    continue
                full = os.path.join(dp, fn)
                if os.path.islink(full):
                    continue
                try:
                    src = open(full, encoding="utf-8", errors="replace").read(READ_CAP)
                except OSError:
                    continue
                for t in others:
                    q = re.escape(t)
                    if re.search(r"""(?:\bfrom|\bimport|\brequire\s*\(|\bimport\s*\()\s*['"]""" + q + r"""(?:['"]|/)""", src):
                        hits.setdefault(name, set()).add((t, _posix(os.path.relpath(full, root))))
    return hits

def executed(output, ws):
    """(실행된 워크스페이스 이름, 러너 출력을 알아봤는가).
    npm:  "> @scope/name@1.0.0 test"   pnpm: "apps/label-printer test$ …" (경로 → 이름)"""
    got = set(re.findall(r"(?m)^>\s+(@?[\w.-]+(?:/[\w.-]+)?)@\S+\s+test\b", output))
    by_dir = {d: n for n, d in ws.items()}
    for path in re.findall(r"(?m)^(.+?)\s+test\$", output):
        got.add(by_dir.get(_posix(path.strip()), path.strip()))
    return got, bool(got)

# ── 상태 ─────────────────────────────────────────────────────────────
def state_path(root, event):
    base = os.environ.get("CLAUDE_PLUGIN_DATA") or os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    d = os.path.join(base, "false-green-state")
    os.makedirs(d, exist_ok=True)
    key = f"{root}\0{event.get('session_id', '')}"
    return os.path.join(d, hashlib.sha256(key.encode()).hexdigest()[:16] + ".json")

def load(path):
    try:
        s = json.load(open(path, encoding="utf-8"))
        if isinstance(s, dict):
            s.setdefault("verdicts", {}); s.setdefault("counts", {}); s.setdefault("log", [])
            return s
    except Exception:
        pass
    return {"verdicts": {}, "counts": {}, "log": []}

def save(path, state):
    state["log"] = state["log"][-200:]
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)

# ── 본체 ─────────────────────────────────────────────────────────────
def session_start(root, path):
    rc, head, _ = run(["git", "rev-parse", "HEAD"], root)
    dirty = (git_paths(["diff", "--name-only", "-z", "HEAD"], root) or []) + \
            (git_paths(["ls-files", "-z", "--others", "--exclude-standard"], root) or [])
    save(path, {"base": head.strip() if rc == 0 else None,
                "snap": blob_hashes(root, sorted(set(dirty))),
                "verdicts": {}, "counts": {}, "log": [{"result": "session-start"}]})

def changed_files(root, state):
    """세션 시작 이후 바뀐 코드 파일. None = 판정 불가(명령 실패)."""
    base = state.get("base")
    if not base:
        return None
    diff = git_paths(["diff", "--name-only", "-z", base], root)
    untracked = git_paths(["ls-files", "-z", "--others", "--exclude-standard"], root)
    if diff is None or untracked is None:
        return None
    snap = state.get("snap", {})
    cand = sorted(set(diff) | set(untracked) | set(snap))
    cur = blob_hashes(root, cand)
    ref = {p: snap[p] for p in cand if p in snap}
    ref.update(base_hashes(root, base, [p for p in cand if p not in snap]))
    return {p for p in cand if cur.get(p) != ref.get(p) and p.endswith(CODE_EXT)}

def main():
    if os.environ.get("COVERAGE_GATE_DISABLE") == "1":
        sys.exit(0)
    try:
        event = json.load(sys.stdin)
    except Exception:
        event = {}
    if not isinstance(event, dict):
        event = {}
    cwd = event.get("cwd") if isinstance(event.get("cwd"), str) else os.getcwd()
    root = repo_root(cwd)
    if not root:
        sys.exit(0)                                  # git 저장소가 아니면 판정하지 않는다
    path = state_path(root, event)

    if "--session-start" in sys.argv:
        session_start(root, path); sys.exit(0)

    state = load(path)
    def skip(why, cache=False, th=None):
        if cache and th:
            state["verdicts"][th] = "pass"
        state["log"].append({"result": "skip", "why": why}); save(path, state); sys.exit(0)

    th = tree_hash(root)
    if th and state["verdicts"].get(th) == "pass":
        sys.exit(0)

    ws = workspaces(root)
    if not ws:
        skip("workspaces 없음", cache=True, th=th)
    changed = changed_files(root, state)
    if changed is None:
        skip("변경을 판정할 수 없다(기준선 없음 또는 git 실패) — 통과를 캐시하지 않는다")
    if not changed:
        skip("코드 변경 없음", cache=True, th=th)

    cons = consumers(root, ws, changed)
    rc, out, err = run("npm test 2>&1", root, timeout=TEST_TIMEOUT, shell=True)
    if rc is None:
        skip(f"테스트 명령 실행 실패/시간초과({TEST_TIMEOUT}s) — 통과를 캐시하지 않는다")
    ran, recognized = executed(out, ws)
    gaps = {n: refs for n, refs in cons.items() if n not in ran} if recognized else {}
    red = rc != 0
    if not gaps and not red:
        if th:
            state["verdicts"][th] = "pass"
        state["log"].append({"result": "pass", "ran": sorted(ran), "recognized": recognized, "consumers": sorted(cons)})
        save(path, state); sys.exit(0)

    vkey = hashlib.sha256(json.dumps([sorted(gaps), red]).encode()).hexdigest()[:12]
    count = state["counts"].get(vkey, 0) + 1          # 트리 해시가 아니라 위반 키로 센다
    state["counts"][vkey] = count
    if count > MAX_REPEAT:
        if th:
            state["verdicts"][th] = "pass"
        state["log"].append({"result": "override", "gaps": sorted(gaps), "red": red, "count": count})
        save(path, state); sys.exit(0)
    state["log"].append({"result": "block", "gaps": sorted(gaps), "red": red, "ran": sorted(ran),
                         "recognized": recognized, "count": count})
    save(path, state)

    lines = ["[coverage-gate] 완료 전에 확인할 것.", ""]
    if red:
        fails = [l for l in out.splitlines() if re.search(r"(✖|not ok|FAIL|Error|failed)", l)][:8]
        lines.append("  ★저장소 전체 테스트(npm test)가 실패한다. 네가 본 초록은 전체가 아니었을 수 있다:")
        lines += [f"      {l.strip()[:150]}" for l in fails] or ["      (실패 줄을 못 뽑았다 — npm test 를 직접 돌려 봐라)"]
        lines.append("")
    if recognized:
        lines.append(f"  테스트가 실제로 실행한 워크스페이스: {', '.join(sorted(ran)) or '(없음)'}")
    for n, refs in sorted(gaps.items()):
        lines.append(f"  실행 안 됨: {n} ({ws[n]})")
        for t, f in sorted(refs)[:5]:
            lines.append(f"      {f}  →  {t} 를 import 한다")
    lines += ["", "  네 변경이 이 코드에서도 올바르게 동작하는지 확인해라.",
              "  확인할 수 없다면 그 사실을 STATUS 에 반영해라."]
    print("\n".join(lines), file=sys.stderr)
    sys.exit(2)

if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:                           # 훅 자신의 결함이 작업을 가두면 안 된다
        print(f"[coverage-gate] 내부 오류로 판정을 건너뛴다: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(0)
