# Postmortem INC-2049: Wrong size chart in the Air Glide order email
Date: 2026-04-24 (Friday). Severity: SEV-3. Owner: Growth.

## What happened
The order email for catalogue Air Glide pairs showed European sizes under US labels, so 1,900 customers saw the wrong size chart for 2 hours.

## Impact
There were 220 size exchanges and 35 returns in the following week.

## Fixes
1. Size labels are now generated from one table.
2. Every email send is reviewed by a second person in Growth.
