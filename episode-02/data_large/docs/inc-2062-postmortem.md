# Postmortem INC-2062
Date: 2026-01-21. Severity: SEV-3. Owner: Payments. Service: payments.

## What happened
The incident was caused by a runaway nightly job. It lasted 140 minutes.

## Impact
About 1,400 customers were affected.

## Fixes
The job now has a time limit and runs on its own machines.
