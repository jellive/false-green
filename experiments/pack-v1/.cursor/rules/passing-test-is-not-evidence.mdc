---
description: Use when citing a passing test as the reason a behaviour is correct or protected - break the responsible code and confirm the test fails, otherwise it constrains nothing
alwaysApply: false
---


# A passing test is not evidence

A test that passes proves the test passed. It does not prove the test would
fail if the behaviour broke.

Assertions on types, truthiness, "does not throw", "is not null" and "contains
a substring" pass for almost any implementation, including an empty one.

## Trigger

You are citing a passing test as your reason for believing a behaviour is
correct or protected.

## Do

Break the responsible code on purpose — delete the body, return a constant —
and re-run the test.

- Test now fails: it constrains the behaviour. Restore the code; the test is
  evidence.
- Test still passes: it constrains nothing. Say so, and do not cite it.

Restore what you broke, and say that you did this check.

## Why this is here

A suite at full coverage stayed green after the function under test was reduced
to returning an empty string. Every assertion in it checked a type.
