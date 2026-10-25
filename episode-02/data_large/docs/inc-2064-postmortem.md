# Postmortem INC-2064
Date: 2026-02-07. Severity: SEV-3. Owner: CX and Fraud. Service: waiting room.

## What happened
The incident was caused by a message queue that filled up. It lasted 95 minutes.

## Impact
About 5,200 customers were affected.

## Fixes
The queue now has a size alert and a second consumer.
