"""Attendance status calculation shared by live scans and historical rows."""

from datetime import datetime
from typing import Any, Mapping


def _minutes(value: str) -> int:
    parsed = datetime.strptime(value, "%H:%M")
    return parsed.hour * 60 + parsed.minute


def calculate_attendance_status(
    time_value: str,
    event_type: str | None,
    settings: Mapping[str, Any],
) -> str:
    """Classify a scan using the configured schedule and minute thresholds."""
    scan_minutes = _minutes(time_value[:5])
    time_key = "time_out" if event_type == "time_out" else "time_in"
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