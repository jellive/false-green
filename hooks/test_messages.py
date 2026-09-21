#!/usr/bin/env python3
"""Tests for the text the agent reads.

test_coverage_gate.py checks exit codes only, so it cannot tell whether a block tells the agent
what to fix. These check the message itself.

  python3 hooks/test_messages.py [hook path]
"""
import ast, glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_coverage_gate as base                # the hook path comes from the same argv

def hangul(s):
    return any("가" <= c <= "힣" for c in s)

TESTS = []
def t(fn): TESTS.append(fn); return fn

@t
def gap_message_names_the_unrun_consumer_in_english():
    d = base.repo(consumer_test=False); g = base.Gate(d); g.start()
    base.edit(d, "packages/lib/index.js", "export const f = 2;\n")
    rc = g.stop()
    return (rc == 2 and not hangul(g.err)
            and "Not run: @x/app (apps/app)" in g.err
            and "apps/app/index.js  →  imports @x/lib" in g.err
            and "If you cannot verify that, say so in your report." in g.err
            and "STATUS" not in g.err)           # STATUS.txt is the benchmark's convention, not the user's

@t
def red_suite_message_is_english():
    d = base.repo(consumer_test=True); g = base.Gate(d); g.start()
    base.edit(d, "apps/app/package.json", json.dumps({"name": "@x/app", "version": "1.0.0", "scripts": {"test": "node -e process.exit(1)"}}))
    base.edit(d, "packages/lib/index.js", "export const f = 2;\n")
    rc = g.stop()
    return rc == 2 and not hangul(g.err) and "full test suite (npm test) is failing" in g.err

@t
def skip_reason_in_the_log_is_english():
    d = base.repo(consumer_test=False, root_pkg={"name": "root", "private": True, "scripts": {"test": "node -e 0"}})
    g = base.Gate(d); g.start(); base.edit(d, "packages/lib/index.js", "export const f = 2;\n")
    rc = g.stop()
    [state] = glob.glob(os.path.join(g.cfg, "false-green-state", "*.json"))
    whys = [e.get("why", "") for e in json.load(open(state, encoding="utf-8"))["log"] if e.get("result") == "skip"]
    return rc == 0 and whys == ["no workspaces"]

@t
def no_korean_string_literal_left_in_the_hook():
    # the scenarios above cannot reach every message (the no-failure-lines fallback, the other skip
    # reasons, a timeout, an internal error), so check every string literal that is not a docstring
    tree = ast.parse(open(base.HOOK, encoding="utf-8").read())
    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                docs.add(id(first.value))
    left = [n.lineno for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs and hangul(n.value)]
    if left:
        print(f"    Korean string literals at lines {sorted(set(left))}")
    return not left

if __name__ == "__main__":
    fails = 0
    for fn in TESTS:
        try:
            ok = fn()
        except Exception as e:
            ok = False; print(f"  ! {fn.__name__}: {type(e).__name__}: {e}")
        print(f"  {'✓' if ok else '✗'} {fn.__name__}")
        fails += not ok
    print(f"\n{len(TESTS) - fails}/{len(TESTS)} passed  ({os.path.basename(base.HOOK)})")
    sys.exit(1 if fails else 0)
