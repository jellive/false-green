---
name: calibrate-before-you-trust
description: Use when a verification script, probe, gate, harness or metric was just written or modified and its output is about to justify a decision - run a known-positive and known-negative first
---

# Calibrate a new check before you trust its answer

A check you just wrote has not been shown to work. Its first clean run is
equally consistent with "nothing is wrong" and "this check cannot detect
anything".

## Trigger

You built or modified a verification script, probe, gate, harness or metric,
and are about to use its output as a reason for a decision.

## Do

Run it against one case it must flag and one case it must pass.

- Different results: the check discriminates. Use it.
- Same result for both: it does not. Fix the check first.

A harness that cannot fail cannot pass either. State that you calibrated it.

## Why this is here

A gate was declared working after reporting zero problems on a repository that
contained nothing it was designed to catch. It was measured against a real
example months later and had never worked.
