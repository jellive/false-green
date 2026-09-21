#!/usr/bin/env python3
"""coverage-gate 재현 테스트. 각 테스트는 코드 리뷰 지적 하나를 재현한다.

  python3 hooks/test_coverage_gate.py [훅 경로]

훅 경로를 바꿔 옛 버전에 돌리면, 고쳐진 지적의 테스트가 옛 버전에서 **실패**해야 한다.
통과만 하는 테스트는 증거가 아니다.
"""
import json, os, subprocess, sys, tempfile, shutil

HOOK = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "coverage-gate.py"))

def sh(cmd, cwd):
    subprocess.run(cmd, cwd=cwd, shell=True, check=True, capture_output=True)

def repo(consumer_test=True, lib_name="packages/lib", extra=None, root_pkg=None, app_src='import { f } from "@x/lib";\n'):
    d = tempfile.mkdtemp()
    w = lambda p, s: (os.makedirs(os.path.dirname(os.path.join(d, p)) or d, exist_ok=True), open(os.path.join(d, p), "w").write(s))
    w("package.json", json.dumps(root_pkg if root_pkg is not None else
      {"name": "root", "private": True, "workspaces": ["packages/*", "apps/*"],
       "scripts": {"test": "npm test --workspaces --if-present"}}))
    w(f"{lib_name}/package.json", json.dumps({"name": "@x/lib", "version": "1.0.0", "scripts": {"test": "node -e 0"}}))
    w(f"{lib_name}/index.js", "export const f = 1;\n")
    app_scripts = {"test": "node -e 0"} if consumer_test else {"start": "node index.js"}
    w("apps/app/package.json", json.dumps({"name": "@x/app", "version": "1.0.0", "scripts": app_scripts}))
    w("apps/app/index.js", app_src)
    for p, s in (extra or {}).items():
        w(p, s)
    sh("git init -q && git add -A && git -c user.name=t -c user.email=t@t commit -qm base", d)
    return d

class Gate:
    def __init__(self, d):
        self.d = d; self.cfg = tempfile.mkdtemp(); self.sid = "s1"
    def start(self):
        return self._call(["--session-start"])
    def stop(self, cwd=None):
        return self._call([], cwd)
    def _call(self, args, cwd=None):
        ev = json.dumps({"cwd": cwd or self.d, "session_id": self.sid, "stop_hook_active": False})
        env = dict(os.environ, CLAUDE_CONFIG_DIR=self.cfg); env.pop("CLAUDE_PLUGIN_DATA", None)
        p = subprocess.run([sys.executable, HOOK, *args], input=ev, capture_output=True, text=True, env=env, timeout=120)
        return p.returncode

def edit(d, p, s):
    os.makedirs(os.path.dirname(os.path.join(d, p)), exist_ok=True); open(os.path.join(d, p), "w").write(s)

TESTS = []
def t(fn): TESTS.append(fn); return fn

# ── 기존 동작 ──
@t
def basic_uncovered_consumer_blocks():
    d = repo(consumer_test=False); g = Gate(d); g.start(); edit(d, "packages/lib/index.js", "export const f = 2;\n")
    return g.stop() == 2
@t
def basic_covered_consumer_passes():
    d = repo(consumer_test=True); g = Gate(d); g.start(); edit(d, "packages/lib/index.js", "export const f = 2;\n")
    return g.stop() == 0
@t
def no_change_passes():
    d = repo(consumer_test=False); g = Gate(d); g.start()
    return g.stop() == 0
@t
def A_cwd_subfolder_still_blocks():
    d = repo(consumer_test=False); g = Gate(d); g.start(); edit(d, "packages/lib/index.js", "export const f = 2;\n")
    return g.stop(cwd=os.path.join(d, "packages/lib")) == 2
@t
def B_agent_commit_still_blocks():
    d = repo(consumer_test=False); g = Gate(d); g.start(); edit(d, "packages/lib/index.js", "export const f = 2;\n")
    sh("git add -A && git -c user.name=t -c user.email=t@t commit -qm agent", d)
    return g.stop() == 2
@t
def red_full_suite_blocks():
    d = repo(consumer_test=True); g = Gate(d); g.start()
    edit(d, "apps/app/package.json", json.dumps({"name": "@x/app", "version": "1.0.0", "scripts": {"test": "node -e process.exit(1)"}}))
    edit(d, "packages/lib/index.js", "export const f = 2;\n")
    return g.stop() == 2

# ── 코드 리뷰 지적 재현 ──
@t
def r7_non_ascii_path_is_seen():
    d = repo(consumer_test=False, extra={"packages/lib/한글.js": "export const k = 1;\n"}); g = Gate(d); g.start()
    edit(d, "packages/lib/한글.js", "export const k = 2;\n")
    return g.stop() == 2
@t
def r12_unknown_runner_does_not_false_block():
    rp = {"name": "root", "private": True, "workspaces": ["packages/*", "apps/*"],
          "scripts": {"test": "node -e \"console.log('app:test: cache miss, executing'); console.log('app:test: PASS')\""}}
    d = repo(consumer_test=False, root_pkg=rp); g = Gate(d); g.start(); edit(d, "packages/lib/index.js", "export const f = 2;\n")
    return g.stop() == 0
@t
def r13_test_that_writes_files_reaches_override():
    rp = {"name": "root", "private": True, "workspaces": ["packages/*", "apps/*"],
          "scripts": {"test": "node -e \"const f='run-counter',s=require('fs');s.writeFileSync(f,String((s.existsSync(f)?+s.readFileSync(f):0)+1))\" && npm test --workspaces --if-present"}}
    d = repo(consumer_test=False, root_pkg=rp); g = Gate(d); g.start(); edit(d, "packages/lib/index.js", "export const f = 2;\n")
    rcs = [g.stop() for _ in range(4)]
    return rcs == [2, 2, 2, 0]
@t
def r3_preexisting_wip_is_not_blamed_on_agent():
    d = repo(consumer_test=False); edit(d, "packages/lib/index.js", "export const f = 99; // 사용자의 WIP\n")
    g = Gate(d); g.start()                       # WIP 는 세션 시작 전에 있었다
    return g.stop() == 0
@t
def r3_agent_reverting_wip_is_seen():
    d = repo(consumer_test=False); edit(d, "packages/lib/index.js", "export const f = 99;\n")
    g = Gate(d); g.start(); sh("git checkout -- packages/lib/index.js", d)
    return g.stop() == 2
@t
def r10_changed_consumer_of_changed_lib_is_checked():
    d = repo(consumer_test=False); g = Gate(d); g.start()
    edit(d, "packages/lib/index.js", "export const f = 2;\n"); edit(d, "apps/app/index.js", 'import { f } from "@x/lib";\nconsole.log(f);\n')
    return g.stop() == 2
@t
def r9_side_effect_import_is_a_consumer():
    d = repo(consumer_test=False, app_src='import "@x/lib";\n'); g = Gate(d); g.start()
    edit(d, "packages/lib/index.js", "export const f = 2;\n")
    return g.stop() == 2
@t
def r15_malformed_root_package_json_does_not_crash():
    d = repo(consumer_test=False); g = Gate(d); g.start()
    edit(d, "package.json", "[]"); edit(d, "packages/lib/index.js", "export const f = 2;\n")
    return g.stop() == 0
@t
def r17_workspace_glob_cannot_escape_repo():
    outside = tempfile.mkdtemp()
    os.makedirs(os.path.join(outside, "victim")); open(os.path.join(outside, "victim/package.json"), "w").write('{"name":"@x/victim"}')
    # from 형태로 쓴다 — 부작용 import 로 쓰면 v2 의 r9 버그(부작용 import 미인식)에 교란돼
    # 저장소 밖을 스캔하고도 소비자로 못 알아봐서 옛 버전에서도 통과해 버린다(실측)
    open(os.path.join(outside, "victim/i.js"), "w").write('import { f } from "@x/lib";\n')
    rel = os.path.relpath(os.path.join(outside, "victim"), tempfile.gettempdir())
    rp = {"name": "root", "private": True, "workspaces": ["packages/*", "apps/*", "../" + rel],
          "scripts": {"test": "npm test --workspaces --if-present"}}
    d = repo(consumer_test=True, root_pkg=rp); g = Gate(d); g.start(); edit(d, "packages/lib/index.js", "export const f = 2;\n")
    return g.stop() == 0                         # 저장소 밖 victim 을 소비자로 보지 않는다

if __name__ == "__main__":
    fails = 0
    for fn in TESTS:
        try:
            ok = fn()
        except Exception as e:
            ok = False; print(f"  ! {fn.__name__}: {type(e).__name__}: {e}")
        print(f"  {'✓' if ok else '✗'} {fn.__name__}")
        fails += not ok
    print(f"\n{len(TESTS) - fails}/{len(TESTS)} 통과  ({os.path.basename(HOOK)})")
    sys.exit(1 if fails else 0)
