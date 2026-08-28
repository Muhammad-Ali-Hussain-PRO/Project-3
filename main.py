"""Interactive demonstration of the ChronosAI scheduling coordinator."""

import time

from database import CalendarDB
from scheduler_agent import ChronosAgent


def run_simulation_matrix() -> None:
    print("=" * 56)
    print(" ChronosAI Agentic Scheduling Engine Core Operational")
    print("=" * 56)
    print()

    db = CalendarDB()
    agent = ChronosAgent(db)
    user_requests = [
        "Schedule a half hour sync with Dave next Tuesday afternoon to audit code bottlenecks",
        "Book a one hour morning sync next Tuesday for structural design review",
    ]

    for index, request in enumerate(user_requests, 1):
        print(f"--- Task Step {index} ---")
        start_perf = time.perf_counter_ns()
        start, end = agent.process_scheduling_intent(request)
        latency_ms = (time.perf_counter_ns() - start_perf) / 1_000_000

        print("[OK] Slot secured successfully")
        print(
            f"[DATE] Assigned Window: {start.strftime('%Y-%m-%d %I:%M %p')} "
            f"to {end.strftime('%I:%M %p')}"
        )
        print(f"[TIME] Optimization Latency: {latency_ms:.3f} ms")
        print()


if __name__ == "__main__":
    run_simulation_matrix()