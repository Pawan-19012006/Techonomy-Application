from datetime import datetime, timezone
from typing import Dict, Any, Optional

from app.database.models import EventModel


class TimerService:
    """Service performing backend event countdown and timer calculation."""

    @staticmethod
    def calculate_event_timer(event: Optional[EventModel]) -> Dict[str, Any]:
        """Calculates timer state for a Competition Event based on current UTC server time.

        Args:
            event: Event database object or None.

        Returns:
            Dict containing remaining_seconds, started, finished, and elapsed_seconds.
        """
        if not event:
            return {
                "remaining_seconds": 0,
                "started": False,
                "finished": False,
                "elapsed_seconds": 0
            }

        now = datetime.now(timezone.utc)
        start = event.start_time
        end = event.end_time

        # Ensure tz-awareness for comparison if naive datetime is passed
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)

        started = now >= start
        finished = now >= end

        if not started:
            remaining_seconds = int((end - start).total_seconds())
            elapsed_seconds = 0
        elif finished:
            remaining_seconds = 0
            elapsed_seconds = int((end - start).total_seconds())
        else:
            remaining_seconds = int((end - now).total_seconds())
            elapsed_seconds = int((now - start).total_seconds())

        return {
            "remaining_seconds": max(0, remaining_seconds),
            "started": started,
            "finished": finished,
            "elapsed_seconds": max(0, elapsed_seconds)
        }
