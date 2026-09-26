# ChronosAI Workspace

A React and Python scheduling prototype that finds the first free interval, explains conflicting events, and requires confirmation before saving a booking. This is an AI-assisted extension of the original ChronosAI command-line prototype. The original `main.py`, `scheduler_agent.py`, and `database.py` remain unchanged at the repository root.

## Try it

- [Public browser demo](https://muhammad-ali-hussain-engineering.muhammadalifarhanhus.chatgpt.site/projects/chronos/)
- [Technical portfolio](https://muhammad-ali-hussain-engineering.muhammadalifarhanhus.chatgpt.site/portfolio/)

The public demo uses React and browser storage with sample data. It does not run the Python service or connect to PostgreSQL. The runnable server version below persists to a relational database. Neither version calls a language model or accesses an external calendar.

## What changed

The earlier prototype used a fixed date, seeded memory, and one-hour conflict shifts. This extension adds editable dates and windows, React state and forms, preview/confirm/delete workflows, HTTP validation, UTC storage, SQL persistence, scoped workspace tokens, idempotent retries, and serialized booking transactions. Both scheduling implementations jump to the end of a blocking event; this avoids skipping shorter free intervals.

## Run with PostgreSQL

Requires Docker Compose. From this `fullstack` directory:

```bash
# Choose your own local development password; use letters and digits for this URL.
printf 'POSTGRES_PASSWORD=replaceWithYourOwnLocalPassword\n' > .env
docker compose up --build
```

Open http://localhost:8000. PostgreSQL is not exposed on a host port. The web app binds only to loopback. The volume retains bookings across restarts. To remove local demo data explicitly: `docker compose down -v`.

## Run with SQLite without Docker

Requires Python 3.11+ and Node.js 22. From `fullstack`:

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell instead: .venv\Scripts\Activate.ps1
pip install -r backend/requirements-dev.txt
cd frontend
npm ci
npm run build
cd ..
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Open http://localhost:8000. The SQLite file is `data/chronos.db`. PostgreSQL is selected instead by setting `DATABASE_URL` to a PostgreSQL connection URL. During frontend development, `npm run dev` proxies `/api` to the local Python service.

## Verify

```bash
python -m pytest backend/tests -q
cd frontend
npm test
npm run test:ui
npm run build
```

`test:ui` builds the isolated browser demo and exercises the rendered React app in a DOM environment. A normal `npm run build` then restores the API-backed build. The GitHub Actions workflow runs the Python suite against both SQLite and PostgreSQL 17 and builds/tests the interface. See `docs/VALIDATION.md` for observed results and limits.

## API

All event endpoints require `Authorization: Bearer <32-128 character random workspace token>`. The interface generates a random token on first use. Only its SHA-256 digest is stored in the database.

| Endpoint | Behavior |
| --- | --- |
| GET /api/health | Storage driver and version |
| GET /api/events | Events for the token's workspace |
| POST /api/suggestions | First free interval and conflicts, without writing |
| POST /api/events | Validate and atomically book a slot; reject overlap |
| DELETE /api/events/{id} | Delete only from the current workspace |

The interactive API schema is at `/docs`. Instants use explicit timezone offsets in requests and UTC epoch milliseconds in stored/public event records. Intervals are half-open: an event ending at 10:00 does not block another starting at 10:00. A request key can replay the same booking safely; a different payload with that key returns 409.

## Boundaries and engineering decisions

- A PostgreSQL transaction advisory lock serializes writes per workspace. SQLite uses `BEGIN IMMEDIATE`. This makes the check and insert atomic for writes through this service. It is not a claim about independently written database clients.
- Workspace tokens are a prototype access boundary, not a complete account system. There is no recovery, rotation interface, user directory, OAuth, or team sharing. Clearing browser storage loses the token. Do not use it for sensitive calendars.
- The public demo keeps records on one device. It has no server-side concurrency guarantee and cannot share calendars across devices.
- Search windows are at most seven days, event durations are 5 minutes to 8 hours, and workspaces are limited to 500 events.
- The UI uses the browser's local timezone. UTC storage is stable across offsets; ambiguous fall-back local times still need an explicit timezone-choice UI before broader calendar use.
- Before public API hosting: add managed accounts, ingress limits, backups, monitoring, retention/deletion controls, and deployment-specific TLS. There are no production users or production-scale benchmarks claimed.

## Next product validation

Ask volunteers to complete three tasks: find a free hour, explain a moved booking, and delete a booking. Record completion and confusion, then revise the interface. This is a proposed user study, not completed customer research.
