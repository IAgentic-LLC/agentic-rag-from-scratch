# Postmortem INC-2061
Date: 2026-01-13. Severity: SEV-1. Owner: Growth. Service: search.

## What happened
The incident was caused by a message queue that filled up. It lasted 18 minutes.

## Impact
About 1,400 customers were affected.

## Fixes
The queue now has a size alert and a second consumer.
