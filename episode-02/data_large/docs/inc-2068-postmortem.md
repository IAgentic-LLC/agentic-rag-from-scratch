# Postmortem INC-2068
Date: 2026-03-04. Severity: SEV-3. Owner: Payments. Service: order tracking.

## What happened
The incident was caused by a database failover that took too long. It lasted 78 minutes.

## Impact
About 980 customers were affected.

## Fixes
The failover timeout was cut from 90 seconds to 20 seconds.
