# Postmortem INC-2060
Date: 2026-01-07. Severity: SEV-3. Owner: Growth. Service: checkout.

## What happened
The incident was caused by an expired security certificate. It lasted 55 minutes.

## Impact
About 2,300 customers were affected.

## Fixes
Certificates now raise an alert 30 days before they expire.
