# Postmortem INC-2078
Date: 2026-05-14. Severity: SEV-3. Owner: Payments. Service: image delivery.

## What happened
The incident was caused by a cache that was cleared by mistake. It lasted 78 minutes.

## Impact
About 240 customers were affected.

## Fixes
Cache clearing now needs a second person to approve it.
