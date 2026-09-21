---
name: zero-findings-is-not-a-pass
description: Use when a check returned 0 results, 0 matches or empty output and you are about to treat it as confirmation - feed it a known-bad case and report the denominator
---

# Zero findings is not a pass

Empty output has two causes that look identical: there was nothing to find, or
the search never looked where you think it looked.

Ignore files, default excludes, a wrong path, an unmatched glob, a filter that
silently drops the interesting case — each produces clean silence.

## Trigger

A check you are relying on returned 0 results, 0 matches, 0 files, or empty
output, and you are about to treat that as confirmation.

## Do

Feed the check something it must flag. If the known-bad case also comes back
clean, the check is not looking and its zero means nothing.

Report the denominator — how many things were examined — alongside the count.
`0 findings` is not a result. `0 findings across 412 files` is.

## Why this is here

A credential scan reported zero. It enumerated files through a tool that honours
ignore files, and the credential lived in an ignored directory. The scan was
working exactly as written and could never have found it.
