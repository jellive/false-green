# false-green

**English** · [한국어](README.ko.md)

**A Stop hook that won't let your coding agent say "done" while the code depending on its change was never run by the tests.**

```
You changed packages/timefmt.
apps/reminder imports it.
Your test command never ran apps/reminder.
```

That's the whole check. It does not judge whether your code is correct — no hook can. It checks whether the
verification you are about to trust actually covered what you changed, and whether it passed.

## Why this exists — and what we measured first

We started by writing a rule pack, the way most agent tooling does: six rules about not trusting a green
light. Then we built a benchmark **before** shipping it, because the first rule was *"a passing test is not
evidence"* and a pack that claims to prevent false completion without measuring it would be refuting itself.

It didn't work.

| | false completions on lying-green cases |
|---|---|
| haiku, no rules | 9/12 |
| haiku, rules in `CLAUDE.md` | 9/12 |
| haiku, rules pasted into the prompt | 6/6 |

Same cases, same model, zero change. The transcripts showed why: the agent ran `npm test` twice, saw green,
and never looked at the package it had broken. The rules were loaded — ask the agent and it could recite them —
but at the moment of deciding, it never reached for them. And the behaviour that actually catches these bugs
(finding everything that depends on what you changed) happens *before* reading a result, not at it.

So we stopped writing rules and wrote a hook that does that check itself.

## What the hook did

The first version passed our own cases and then **broke on a held-out case built after it was frozen** — three
bugs, all of which only showed up because we kept the hook's decision log next to each run:

- it trusted the hook's `cwd`, which follows the agent when it `cd`s into a subfolder
- it compared against `HEAD`, so committing its own work blinded it
- it guessed pnpm's output format wrong and blocked on a consumer that *had* run

We fixed those, froze v2, built a **new** held-out case (same principle, different surface), and measured again:

| held-out case | baseline | with the hook |
|---|---|---|
| false completion | **3/3** | 0/3 |
| sound completion (oracle passed) | 0/3 | **3/3** |

Every treated run followed the same path — the agent tried to finish with a broken consumer, the hook named
it, the agent fixed it:

```
block · uncovered: @due/reminder  →  pass  →  COMPLETE, hidden oracle PASS
```

On an honest twin (where the tests genuinely cover everything) the hook never fired and all three runs completed normally.

**n = 3, one held-out case, one model.** That is a direction, not a statistic. Full numbers, the failures, and
everything the numbers do not say are in [`RESULTS.md`](RESULTS.md) (in Korean).

Those numbers are for v2. The version shipped here is v3, which fixes nine bugs found in code review. We
re-ran it: false completions stayed at zero and the held-out case stayed at 3/3 fixed — but on one of our own
cases it fixed fewer (2/3 → 0/3), because v3 lets the agent through after three identical blocks instead of
blocking indefinitely. The agents it let through all reported the work as unfinished rather than claiming it was done.

## What it catches, and what it doesn't

Catches, in npm and pnpm workspaces:

- a package that depends on your change but has no test script
- a package whose tests exist but that the root test command filters or leaves out of an explicit list
- a narrow green — you ran one package's tests, but the full suite is red

Does **not** catch, by design:

- tests that run but assert nothing meaningful
- a scan or linter whose file list silently skips what matters
- anything outside a JS workspace

With a runner it doesn't recognise (turbo, nx, a custom script), it can't tell which packages ran, so it skips the
coverage check and only blocks if the full test command fails.

It also can be satisfied without being honoured — `"test": "true"` in a skipped package will pass the gate.
We haven't seen an agent do it in our runs. That's not the same as it not happening.

## Security

**This hook runs your repository's test command** (`npm test`) when the agent tries to stop. That is the
mechanism — it can't check what the tests cover without running them. It is the same trust boundary as the
agent running `npm test` itself, but it happens automatically. Don't enable it on repositories you wouldn't
run the tests of. Turn it off for a session with `COVERAGE_GATE_DISABLE=1`.

## Install (Claude Code)

```
/plugin marketplace add jellive/false-green
/plugin install false-green@false-green
```

Or for a single session without installing: `claude --plugin-dir path/to/false-green`.

The hook re-runs your test command when the agent tries to stop, so on large repos it costs one extra test
run per stop attempt (timeout: `COVERAGE_GATE_TIMEOUT`, default 600s — on timeout it skips rather than blocks).
It blocks at most three times on the same unresolved finding, then lets the agent through and records the
override. Changes you had in progress before the session started are not blamed on the agent.

`hooks/test_coverage_gate.py` reproduces every bug found in review; run it against an older hook version in
`hooks/history/` and the fixed cases fail (`python3 hooks/test_coverage_gate.py hooks/history/coverage-gate.v2.py` → 6/15).

## The benchmark

Every case is an ordinary work request — nothing tells the agent to distrust its tools. After the agent
exits, a hidden oracle it never saw checks what actually shipped. Each lying-green case has an honest twin,
so an agent that answers "not done" to everything can't score well.

```bash
export FG_AGENT="$PWD/harness/stubs/claude-clean-trace.sh" FG_MODEL=haiku
./harness/run.sh fg6-allowlist-misses-new-app 3 baseline
FG_AGENT="$PWD/harness/stubs/claude-hook-trace.sh" ./harness/run.sh fg6-allowlist-misses-new-app 3 hook
python3 harness/grade.py runs/*.jsonl
python3 harness/gate_paths.py hook          # how each run got past the gate
```

Bring your own adapter for another agent: read the task on stdin, work in the current directory, leave a `STATUS.txt`.

`experiments/pack-v1/` keeps the rule pack that didn't work, and why. `benchmarks/parked/` keeps the cases
that didn't become cases, including one mechanism that turned out not to reproduce on macOS at all.

## License

MIT
