# Architecture and interview walkthrough

The React form collects a title, local date, time window and duration. Date inputs become offset-aware ISO instants before HTTP requests. The API validates types, offsets, duration and search bounds. A SHA-256 workspace identifier scopes all SQL queries. The scheduling engine returns a proposal without writing. Confirmation takes a transaction lock, checks the idempotency key, checks overlaps again, and inserts only if still free.

## Failure scenarios to explain

1. Two requests choose the same slot: both previews can succeed; exactly one overlapping confirmation commits through the API.
2. A client retries after a lost response: the same request key and payload return the original event.
3. A key is reused with changed content: reject it rather than silently returning unrelated data.
4. A different workspace requests an event ID: deletion affects no row and returns 404.
5. A slot ends at another event's start: half-open interval semantics permit the boundary.
6. A process restarts: database rows remain; workspace access still requires the same client token.

## Complexity and tradeoffs

The current engine sorts n events, then scans them: O(n log n) time and O(n) working space. At the prototype's 500-event bound, a simple scan is easier to inspect than an interval tree. A compound workspace/start index supports scoped reads; larger calendars would need bounded date queries and pagination. Preview results may become stale, so correctness belongs to the confirmation transaction.

## Development provenance

This extension was built with AI assistance for Muhammad Ali Hussain's engineering portfolio. Review and understand the implementation before representing personal proficiency. The code and tests are evidence of an implementation, not evidence of independent interview readiness or production experience.

## Practice tasks

- Explain the overlap predicate with a boundary example.
- Add a 75-minute duration option, test it, and trace the request through each layer.
- Reproduce the five-writer race test and explain why a frontend-only check is insufficient.
- Add one field to the event schema and handle old records safely.
- Explain the distinction between a browser demo, a local API, and a production service.
- Describe one product change you would make after observing a user struggle.
