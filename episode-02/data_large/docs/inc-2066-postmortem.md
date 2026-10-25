# Postmortem INC-2066
Date: 2026-02-16. Severity: SEV-2. Owner: Logistics. Service: image delivery.

## What happened
The incident was caused by a memory leak introduced by a release. It lasted 120 minutes.

## Impact
About 5,200 customers were affected.

## Fixes
The release was rolled back and a memory alert was added.
