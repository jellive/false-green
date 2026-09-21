# false-green


A command exiting 0 is not evidence. It is one observation, and the thing that
produced it can be wrong in ways that produce no error at all.

These rules exist because each one was learned the expensive way. Triggers are
observable facts, not judgment calls. "It seems fine" is not a trigger.

## 1. Count what actually ran

An orchestrator that exits 0 has not told you that everything ran. Runners skip
units that declare no task, path filters skip jobs, and a skipped unit and a
passing unit produce the same green.

**Trigger:** you are about to treat a multi-unit command (test runner, monorepo
task runner, CI, linter across packages) as covering everything.

**Do:** count the units that actually executed and compare that number against
the units that exist. If the two differ, say which ones were not covered. Name
the number in your report, not the word "all".

## 2. Zero findings is not a pass

Empty output has two causes that look identical: there was nothing to find, or
the search never looked where you think it looked. Filters, ignore files,
default excludes and wrong paths all produce clean silence.

**Trigger:** a check you are relying on returned 0 results, 0 matches, 0 files,
or empty output.

**Do:** before believing it, feed the check something it must flag. If the
known-bad case also comes back clean, the check is not looking. Report the
denominator — how many things were examined — not just the count of findings.

## 3. A passing test is not evidence that the behaviour is held

A test that passes proves the test passed. It does not prove the test would
fail if the behaviour broke. Assertions on types, truthiness, "does not throw"
and "is not null" pass for almost any implementation.

**Trigger:** you are citing a passing test as your reason for believing a
behaviour is correct or protected.

**Do:** break the responsible code on purpose — delete the body, return a
constant — and re-run. If the test still passes, it constrains nothing and is
not evidence. Restore the code afterwards. Say that you did this.

## 4. Verify the thing that ships, not the thing you edited

What you changed and what consumers load are not always the same file. Build
outputs, caches, compiled bytecode, installed copies and already-running
processes can all serve the old version while your source looks correct.

**Trigger:** the project has a build step, a generated output directory, a cache,
an already-running server, or an entry point that differs from the file you edited.

**Do:** find what consumers actually load — the package entry point, the served
process, the installed copy — and check the new behaviour there. If a build is
required to propagate your change, run it before you judge.

## 5. An exit code read through a pipe is not the command's

The exit status of a pipeline is the last stage's unless the shell is told
otherwise, and some consumers close the pipe early enough to kill the producer.
Truncating output with head or tail also removes the part where the verdict was.

**Trigger:** you are judging success or failure from a command that was piped,
chained, or truncated.

**Do:** write the output to a file, capture the status of the command itself,
and read the file. Do not conclude from the tail alone.

## 6. Calibrate a new check before you trust its answer

A check you just wrote has not been shown to work. Its first clean run is
equally consistent with "nothing is wrong" and "this check cannot detect
anything".

**Trigger:** you built or modified a verification script, probe, gate or
harness, and are about to use its output as a reason.

**Do:** run it against one case it must flag and one case it must pass. If both
come back the same, fix the check before using it. A harness that cannot fail
cannot pass either.

## Reporting

When you state that work is complete, state what you ran and what it covered.
If some part could not be verified, say which part and why — "not verified" is
a useful, honest answer. "It should work" is not a verification.
