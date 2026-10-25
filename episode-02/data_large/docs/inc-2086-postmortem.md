# Postmortem INC-2086
Date: 2026-06-29. Severity: SEV-1. Owner: Platform. Service: order emails.

## What happened
The incident was caused by a runaway nightly job. It lasted 95 minutes.

## Impact
About 5,200 customers were affected.

## Fixes
The job now has a time limit and runs on its own machines.
