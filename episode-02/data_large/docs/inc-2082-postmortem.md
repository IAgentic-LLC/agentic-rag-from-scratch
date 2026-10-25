# Postmortem INC-2082
Date: 2026-06-05. Severity: SEV-2. Owner: CX and Fraud. Service: admin panel.

## What happened
The incident was caused by a memory leak introduced by a release. It lasted 33 minutes.

## Impact
About 5,200 customers were affected.

## Fixes
The release was rolled back and a memory alert was added.
