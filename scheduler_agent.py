"""Natural-language scheduling agent and conflict-resolution heuristics."""

from datetime import datetime, timedelta

from database import CalendarDB


class ChronosAgent:
    """Parse supported scheduling language and reserve the first free slot."""

    def __init__(self, db: CalendarDB) -> None:
        self.db = db

    def process_scheduling_intent(self, natural_language_text: str) -> tuple[datetime, datetime]:
        """Interpret a request, resolve conflicts, and register the chosen slot."""
        print(f'[ChronosAgent] Analyzing Request: "{natural_language_text}"')

        duration_hours = 0.5 if "half hour" in natural_language_text.lower() or "30 min" in natural_language_text.lower() else 1.0
        target_hour = 14 if "afternoon" in natural_language_text.lower() else 9
        proposed_start = datetime(2026, 9, 1, target_hour)
        proposed_end = proposed_start + timedelta(hours=duration_hours)

        conflict, conflict_title = self.db.check_conflict(proposed_start, proposed_end)
        if conflict:
            print(f'[CONFLICT] Overlap detected with existing block: "{conflict_title}"')
            print("[RESOLVING] Invoking rescheduling heuristic logic block...")

        while conflict:
            proposed_start += timedelta(hours=1)
            proposed_end = proposed_start + timedelta(hours=duration_hours)
            conflict, conflict_title = self.db.check_conflict(proposed_start, proposed_end)

        self.db.insert_event("AI Scheduled Sync", proposed_start, proposed_end)
        return proposed_start, proposed_end