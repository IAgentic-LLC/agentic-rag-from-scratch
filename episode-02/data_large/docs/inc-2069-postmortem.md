# Postmortem INC-2069
Date: 2026-03-12. Severity: SEV-3. Owner: Logistics. Service: returns portal.

## What happened
The incident was caused by a memory leak introduced by a release. It lasted 185 minutes.

## Impact
About 1,400 customers were affected.

## Fixes
The release was rolled back and a memory alert was added.
