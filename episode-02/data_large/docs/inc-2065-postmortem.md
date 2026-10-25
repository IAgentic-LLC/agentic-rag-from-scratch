# Postmortem INC-2065
Date: 2026-02-11. Severity: SEV-3. Owner: CX and Fraud. Service: order emails.

## What happened
The incident was caused by a runaway nightly job. It lasted 120 minutes.

## Impact
About 5,200 customers were affected.

## Fixes
The job now has a time limit and runs on its own machines.
