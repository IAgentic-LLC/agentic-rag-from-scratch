# Postmortem INC-2077
Date: 2026-05-10. Severity: SEV-2. Owner: Logistics. Service: order emails.

## What happened
The incident was caused by a memory leak introduced by a release. It lasted 55 minutes.

## Impact
About 410 customers were affected.

## Fixes
The release was rolled back and a memory alert was added.
