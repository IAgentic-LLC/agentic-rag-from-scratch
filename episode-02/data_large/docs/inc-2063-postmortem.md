# Postmortem INC-2063
Date: 2026-01-29. Severity: SEV-2. Owner: Growth. Service: inventory.

## What happened
The incident was caused by a database failover that took too long. It lasted 78 minutes.

## Impact
About 3,100 customers were affected.

## Fixes
The failover timeout was cut from 90 seconds to 20 seconds.
