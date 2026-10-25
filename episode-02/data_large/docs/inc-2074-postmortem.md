# Postmortem INC-2074
Date: 2026-04-20. Severity: SEV-3. Owner: Logistics. Service: payments.

## What happened
The incident was caused by a memory leak introduced by a release. It lasted 95 minutes.

## Impact
About 240 customers were affected.

## Fixes
The release was rolled back and a memory alert was added.
