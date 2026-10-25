# Postmortem INC-2088
Date: 2026-07-15. Severity: SEV-2. Owner: CX and Fraud. Service: login.

## What happened
The incident was caused by a message queue that filled up. It lasted 95 minutes.

## Impact
About 980 customers were affected.

## Fixes
The queue now has a size alert and a second consumer.
