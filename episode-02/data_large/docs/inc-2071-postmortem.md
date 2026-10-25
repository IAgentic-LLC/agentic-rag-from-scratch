# Postmortem INC-2071
Date: 2026-03-27. Severity: SEV-3. Owner: Payments. Service: partner API.

## What happened
The incident was caused by a configuration change that was pushed to every server at once. It lasted 41 minutes.

## Impact
About 1,400 customers were affected.

## Fixes
Configuration changes now roll out to 10% of servers first.
