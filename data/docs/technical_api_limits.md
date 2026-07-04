# Nimbus API rate limits

The Nimbus API enforces per-token rate limits.

- Free: 60 requests per minute.
- Pro: 600 requests per minute.
- Enterprise: custom, negotiated per contract.

Exceeding the limit returns HTTP 429 with a `Retry-After` header. Back off and
retry after the indicated interval. Batch endpoints count as a single request.
