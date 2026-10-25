# Postmortem INC-2073
Date: 2026-04-13. Severity: SEV-2. Owner: Payments. Service: search.

## What happened
The incident was caused by an expired security certificate. It lasted 41 minutes.

## Impact
About 5,200 customers were affected.

## Fixes
Certificates now raise an alert 30 days before they expire.
