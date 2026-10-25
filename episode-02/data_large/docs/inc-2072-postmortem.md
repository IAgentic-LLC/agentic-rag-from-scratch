# Postmortem INC-2072
Date: 2026-04-04. Severity: SEV-1. Owner: Payments. Service: checkout.

## What happened
The incident was caused by a message queue that filled up. It lasted 140 minutes.

## Impact
About 5,200 customers were affected.

## Fixes
The queue now has a size alert and a second consumer.
