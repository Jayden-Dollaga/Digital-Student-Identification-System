"""School calendar exceptions: holidays, class suspensions, half-days.

Storage lives in settings.json under "school_calendar", keyed by
"YYYY-MM-DD" - see settings_store.default_settings for the shape. Only
exception dates are stored; a normal school day has no entry.

This module is the single place that understands the entry shape, so
core.attendance_status (per-date schedule override) and gui_web.api
(attendance evaluation report, calendar CRUD) both read/write through it
instead of each re-implementing the same date parsing and validation.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, Mapping, Optional, Tuple

VALID_TYPES = ("holiday", "suspension", "half_day")

# Both "holiday" and "suspension" mean "no attendance expected" - they're
# kept as distinct types purely so admins can see *why* a day was off
# (a fixed calendar holiday vs. an ad-hoc weather/emergency suspension).
# Attendance math treats them identically.
NON_SCHOOL_DAY_TYPES = ("holiday", "suspension")

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _is_valid_date_string(date_str: str) -> bool:
    if not _DATE_RE.match(date_str or ""):
        return False
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _is_valid_time_string(value: str) -> bool:
    try:
        datetime.strptime(value, "%H:%M")
        return True
    except (ValueError, TypeError):
        return False


def _minutes(value: str) -> int:
    parsed = datetime.strptime(value, "%H:%M")
    return parsed.hour * 60 + parsed.minute


def get_calendar(settings: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    calendar = settings.get("school_calendar")
    return calendar if isinstance(calendar, dict) else {}


def get_entry(settings: Mapping[str, Any], date_str: str) -> Optional[Dict[str, Any]]:
    return get_calendar(settings).get(date_str)


def is_non_school_day(settings: Mapping[str, Any], date_str: str) -> bool:
    entry = get_entry(settings, date_str)
    return bool(entry) and entry.get("type") in NON_SCHOOL_DAY_TYPES


def get_schedule_for_date(
    settings: Mapping[str, Any], date_str: str, event_type: Optional[str] = None
) -> Tuple[str, str]:
    """Return (time_in, time_out) that should apply on this date.

    A half_day entry overrides the global schedule for that date only;
    everything else falls back to the normal settings.json time_in/time_out.
    """
    default_time_in = str(settings.get("time_in", "08:00"))
    default_time_out = str(settings.get("time_out", "17:00"))
    entry = get_entry(settings, date_str)
    if entry and entry.get("type") == "half_day":
        time_in = entry.get("time_in") or default_time_in
        time_out = entry.get("time_out") or default_time_out
        return str(time_in), str(time_out)
    return default_time_in, default_time_out


def validate_entry(
    entry_type: str,
    time_in: Optional[str] = None,
    time_out: Optional[str] = None,
) -> Optional[str]:
    """Return an error message if this entry is unusable, else None."""
    if entry_type not in VALID_TYPES:
        return f"Unknown calendar entry type: {entry_type!r}."
    if entry_type == "half_day":
        if not time_in or not _is_valid_time_string(time_in):
            return "Half-day entries need a valid time_in (HH:MM)."
        if not time_out or not _is_valid_time_string(time_out):
            return "Half-day entries need a valid time_out (HH:MM)."
        if _minutes(time_out) <= _minutes(time_in):
            return "Half-day time_out must be later than time_in."
    return None


def set_entry(
    settings: Dict[str, Any],
    date_str: str,
    entry_type: str,
    label: str = "",
    time_in: Optional[str] = None,
    time_out: Optional[str] = None,
) -> Dict[str, Any]:
    """Create or overwrite a calendar entry. Raises ValueError if invalid."""
    if not _is_valid_date_string(date_str):
        raise ValueError(f"Invalid date: {date_str!r} (expected YYYY-MM-DD).")
    error = validate_entry(entry_type, time_in, time_out)
    if error:
        raise ValueError(error)

    entry: Dict[str, Any] = {"type": entry_type, "label": (label or "").strip()[:200]}
    if entry_type == "half_day":
        entry["time_in"] = time_in
        entry["time_out"] = time_out

    calendar = dict(get_calendar(settings))
    calendar[date_str] = entry
    settings["school_calendar"] = calendar
    return settings


def remove_entry(settings: Dict[str, Any], date_str: str) -> Dict[str, Any]:
    calendar = dict(get_calendar(settings))
    calendar.pop(date_str, None)
    settings["school_calendar"] = calendar
    return settings
