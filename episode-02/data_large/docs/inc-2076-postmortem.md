# Postmortem INC-2076
Date: 2026-05-05. Severity: SEV-3. Owner: Payments. Service: waiting room.

## What happened
The incident was caused by a database failover that took too long. It lasted 64 minutes.

## Impact
About 5,200 customers were affected.

## Fixes
The failover timeout was cut from 90 seconds to 20 seconds.
