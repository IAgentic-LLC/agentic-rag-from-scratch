# Partner API Changelog
Owner: Platform. Last reviewed: 2026-07-08.

## Version 2
Version 2 launched on 2026-03-02. It renamed the field order_ref to reference and returns prices in cents as integers.

## Version 1
Version 1 allowed 60 requests per minute with no burst. Version 1 was shut down on 2026-06-30; calls to it now return HTTP 410.

## Limits
Rate limits are counted per API key, not per IP address. Two partner systems that share one key share one limit.
