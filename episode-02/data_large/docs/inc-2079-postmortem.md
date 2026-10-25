# Postmortem INC-2079
Date: 2026-05-22. Severity: SEV-1. Owner: Logistics. Service: login.

## What happened
The incident was caused by a database failover that took too long. It lasted 120 minutes.

## Impact
About 410 customers were affected.

## Fixes
The failover timeout was cut from 90 seconds to 20 seconds.
