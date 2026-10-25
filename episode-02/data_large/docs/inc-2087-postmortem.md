# Postmortem INC-2087
Date: 2026-07-06. Severity: SEV-3. Owner: Growth. Service: order emails.

## What happened
The incident was caused by a configuration change that was pushed to every server at once. It lasted 18 minutes.

## Impact
About 5,200 customers were affected.

## Fixes
Configuration changes now roll out to 10% of servers first.
