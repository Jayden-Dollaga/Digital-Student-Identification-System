"""Attendance status calculation shared by live scans and historical rows."""

from datetime import datetime
from typing import Any, Mapping, Optional

from core import attendance_calendar


def _minutes(value: str) -> int:
    parsed = datetime.strptime(value, "%H:%M")
    return parsed.hour * 60 + parsed.minute


def calculate_attendance_status(
    time_value: str,
    event_type: str | None,
    settings: Mapping[str, Any],
    date_value: Optional[str] = None,
) -> str:
    """Classify a scan using the configured schedule and minute thresholds.

    `date_value` (YYYY-MM-DD) is optional and only matters if that date has
    a half_day entry in the school calendar (Settings > Calendar) - when it
    does, that date's own time_in/time_out is used instead of the global
    schedule, so a half-day dismissal at noon isn't flagged "Early" against
    the normal 17:00 expectation. Omitting it (existing callers) preserves
    the previous global-schedule-only behavior exactly.
    """
    scan_minutes = _minutes(time_value[:5])
    time_key = "time_out" if event_type == "time_out" else "time_in"

    if date_value:
        day_time_in, day_time_out = attendance_calendar.get_schedule_for_date(settings, date_value)
        expected = _minutes(day_time_out if time_key == "time_out" else day_time_in)
    else:
        default_time = "17:00" if time_key == "time_out" else "08:00"
        expected = _minutes(str(settings.get(time_key, default_time)))

    early = max(0, int(settings.get("early_threshold_minutes", 15)))
    late = max(0, int(settings.get("late_threshold_minutes", 15)))
    absent = max(0, int(settings.get("absent_threshold_minutes", 0)))

    if time_key == "time_out":
        return "Early" if scan_minutes < expected - early else "Present"
    if scan_minutes < expected - early:
        return "Early"
    if absent > 0 and scan_minutes > expected + absent:
        return "Absent"
    if scan_minutes > expected + late:
        return "Late"
    return "Present"