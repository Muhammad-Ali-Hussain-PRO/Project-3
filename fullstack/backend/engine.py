"""Deterministic interval scheduling. All instants are UTC epoch milliseconds."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Slot:
    start: int
    end: int
    conflicts: list[dict]


def first_available(earliest: int, latest: int, duration_minutes: int, events: list[dict]) -> Slot | None:
    duration = duration_minutes * 60_000
    cursor = earliest
    conflicts = []
    for event in sorted(events, key=lambda e: (e['start'], e['end'])):
        if event['end'] <= cursor:
            continue
        if cursor + duration <= event['start']:
            break
        if cursor < event['end'] and cursor + duration > event['start']:
            conflicts.append({'title': event['title'], 'start': event['start'], 'end': event['end']})
            cursor = event['end']
        if cursor + duration > latest:
            return None
    return Slot(cursor, cursor + duration, conflicts) if cursor + duration <= latest else None
