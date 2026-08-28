# ChronosAI Scheduler

ChronosAI Scheduler is a compact Python demonstration of an agentic calendar
workflow. It turns natural-language requests into scheduled events, evaluates
overlap boundaries against calendar memory, and moves conflicting meetings to
the next available hourly slot.

## Architecture

- `main.py` runs the multi-request orchestration sandbox and reports latency.
- `scheduler_agent.py` extracts duration and time-window intent, then resolves conflicts.
- `database.py` provides seeded in-memory calendar storage and overlap checks.
- `.github/workflows/agent-test.yml` runs the simulation on pushes and pull requests.

The current sandbox uses deterministic heuristics so it runs without API keys or
external services. The agent boundary is isolated in `ChronosAgent`, making it a
natural place to add an LLM parser and tool-calling layer later.

## Run locally

Requires Python 3.11 or newer.

```bash
python main.py
```

The seeded Tuesday calendar contains events at 2:00 PM and 4:00 PM. The sample
afternoon request therefore demonstrates automatic conflict resolution, while
the morning request demonstrates a direct booking.

## Example output

```text
[CONFLICT] Overlap detected with existing block: "Google Infrastructure Review"
[RESOLVING] Invoking rescheduling heuristic logic block...
[OK] Slot secured successfully
[DATE] Assigned Window: 2026-09-01 03:00 PM to 03:30 PM
```