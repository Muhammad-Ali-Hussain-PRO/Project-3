# Validation record

Checked on 26 September 2026.

- Python API and SQLite suite: 30 cases passed, including persistence after restart, token isolation, invalid timestamps, duplicate retries, five simultaneous conflicting writes, five simultaneous identical retries, and 200 seeded engine comparisons against a minute-by-minute reference.
- JavaScript scheduling suite: 8 cases passed for interval boundaries, nested conflicts, no-slot outcomes, input validation, and non-mutation.
- Rendered React DOM flow: sample agenda, conflict explanation, confirmation, deletion, reset, and associated input labels passed.
- Optimized frontend build completed successfully.
- PostgreSQL 17 integration is configured in GitHub Actions. Its result must be checked on the linked commit; a local PostgreSQL server was unavailable in the authoring environment.

These are development checks on deterministic test inputs. No production traffic, customer research, performance improvement, browser accessibility certification, or Docker end-to-end execution is claimed. The public browser demo intentionally uses device-local storage; the SQL service has a different persistence and concurrency boundary.
