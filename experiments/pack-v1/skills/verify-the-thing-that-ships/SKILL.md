---
name: verify-the-thing-that-ships
description: Use when the project has a build step, generated output, a cache, a running process or an entry point different from the edited file - verify the artifact consumers actually load
---

# Verify the thing that ships

What you changed and what consumers load are not always the same file.

Build outputs, caches, compiled bytecode, installed copies and already-running
processes can all keep serving the old version while your source reads
perfectly correct.

## Trigger

The project has a build step, a generated output directory, a cache, an
already-running process, or a declared entry point that differs from the file
you edited.

## Do

Find what consumers actually load — the declared entry point, the served
process, the installed copy — and check the new behaviour there, not in the
file you edited. If a build must run for the change to propagate, run it before
you judge.

## Why this is here

A mutation sweep reported every mutant surviving. The runner had reused a
process that was already listening on the port, so not one source change had
reached the code being measured. The conclusion — "these tests are weak" —
was the exact opposite of the truth.
