# Postmortem INC-2084
Date: 2026-06-16. Severity: SEV-3. Owner: Logistics. Service: payments.

## What happened
The incident was caused by a database failover that took too long. It lasted 25 minutes.

## Impact
About 980 customers were affected.

## Fixes
The failover timeout was cut from 90 seconds to 20 seconds.
