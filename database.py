"""In-memory calendar storage used by the ChronosAI scheduler."""

from datetime import datetime


class CalendarDB:
    """Small calendar repository with overlap detection and event insertion."""

    def __init__(self) -> None:
        self.events = [
            {
                "summary": "Google Infrastructure Review",
                "start": datetime(2026, 9, 1, 14, 0),
                "end": datetime(2026, 9, 1, 15, 0),
            },
            {
                "summary": "OpenAI Paper Discussion",
                "start": datetime(2026, 9, 1, 16, 0),
                "end": datetime(2026, 9, 1, 17, 0),
            },
        ]

    def check_conflict(
        self, start_time: datetime, end_time: datetime
    ) -> tuple[bool, str | None]:
        """Return whether a proposed interval overlaps an existing event."""
        for event in self.events:
            if start_time < event["end"] and end_time > event["start"]:
                return True, event["summary"]
        return False, None

    def insert_event(
        self, summary: str, start_time: datetime, end_time: datetime
    ) -> None:
        """Persist a newly scheduled event in the in-memory calendar."""
        self.events.append(
            {"summary": summary, "start": start_time, "end": end_time}
        )