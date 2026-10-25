# Postmortem INC-2052: Carrier delay for EU parcels
Date: 2026-07-17 (Friday). Severity: SEV-2. Owner: Logistics.

## What happened
A carrier hub in Cologne closed for 3 days after a strike. About 2,400 EU parcels were delayed by 2 to 4 days.

## Impact
Customers saw delivery estimates that were too early. Support received 310 extra contacts.

## Fixes
1. Move EU parcels to a second carrier when a hub is closed.
2. Add a banner to order pages when delivery estimates are at risk.
