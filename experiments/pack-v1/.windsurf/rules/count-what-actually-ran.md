---
description: Use when a multi-unit command (monorepo runner, test suite, CI, workspace linter) exited 0 and you are about to treat it as covering everything - count executed units against declared units before claiming coverage
alwaysApply: false
---


# Count what actually ran

An orchestrator that exits 0 has not told you that everything ran.

Test runners skip packages that declare no test task. CI path filters skip
whole jobs. A skipped unit and a passing unit produce the same green, and the
skipped one usually leaves no line in the log at all.

## Trigger

You are about to treat a multi-unit command — a monorepo task runner, a test
suite across packages, CI, a linter over a workspace — as covering everything.

## Do

Count the units that actually executed. Compare that number against the units
that exist. Report the number, not the word "all".

```
units declared : 3
units executed : 2        <- the third declared no task and was skipped in silence
```

If the two differ, name what was not covered before you call the work done.

## Why this is here

A dependency upgrade was committed against a green run that never touched the
package the upgrade affected. The same upgrade broke a sibling project where
the task happened to be declared — so the failure was real, and the green was
the only thing that differed.
