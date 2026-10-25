# Postmortem INC-2089
Date: 2026-07-21. Severity: SEV-3. Owner: CX and Fraud. Service: image delivery.

## What happened
The incident was caused by an expired security certificate. It lasted 33 minutes.

## Impact
About 410 customers were affected.

## Fixes
Certificates now raise an alert 30 days before they expire.
