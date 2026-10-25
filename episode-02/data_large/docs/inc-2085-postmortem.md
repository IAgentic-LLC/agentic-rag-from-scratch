# Postmortem INC-2085
Date: 2026-06-20. Severity: SEV-1. Owner: Logistics. Service: image delivery.

## What happened
The incident was caused by a memory leak introduced by a release. It lasted 18 minutes.

## Impact
About 240 customers were affected.

## Fixes
The release was rolled back and a memory alert was added.
