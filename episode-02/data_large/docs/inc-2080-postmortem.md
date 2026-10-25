# Postmortem INC-2080
Date: 2026-05-26. Severity: SEV-2. Owner: Platform. Service: order tracking.

## What happened
The incident was caused by a message queue that filled up. It lasted 120 minutes.

## Impact
About 240 customers were affected.

## Fixes
The queue now has a size alert and a second consumer.
