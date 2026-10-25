# Postmortem INC-2081
Date: 2026-05-30. Severity: SEV-2. Owner: Payments. Service: returns portal.

## What happened
The incident was caused by an expired security certificate. It lasted 12 minutes.

## Impact
About 2,300 customers were affected.

## Fixes
Certificates now raise an alert 30 days before they expire.
