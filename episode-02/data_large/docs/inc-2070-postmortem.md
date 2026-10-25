# Postmortem INC-2070
Date: 2026-03-19. Severity: SEV-2. Owner: CX and Fraud. Service: admin panel.

## What happened
The incident was caused by a runaway nightly job. It lasted 140 minutes.

## Impact
About 5,200 customers were affected.

## Fixes
The job now has a time limit and runs on its own machines.
