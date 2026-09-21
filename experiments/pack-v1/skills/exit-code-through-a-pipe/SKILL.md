---
name: exit-code-through-a-pipe
description: Use when judging success or failure from a piped, chained or truncated command - capture the command's own status to a file instead of reading the tail
---

# An exit code read through a pipe is not the command's

The exit status of a pipeline is the last stage's unless the shell is told
otherwise. A consumer that stops early can also kill the producer, turning a
success into a failure.

Truncating output with `head` or `tail` removes the part where the verdict was.

## Trigger

You are judging success or failure from a command that was piped, chained, or
truncated.

## Do

Write the output to a file, capture the status of the command itself, then read
the file.

```
cmd > out.log 2>&1; rc=$?
```

Do not conclude from the tail alone — for many tools the conclusion is not the
last line.

## Why this is here

A backup check reported a directory missing from an archive that contained
thirty-three files from it. The consumer matched on the first line and closed
the pipe; the producer died of it; the pipeline reported failure. The archive
was fine the whole time.
