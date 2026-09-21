import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from core.attendance_status import calculate_attendance_status


SETTINGS = {
    "time_in": "08:00",
    "time_out": "17:00",
    "early_threshold_minutes": 15,
    "late_threshold_minutes": 15,
    "absent_threshold_minutes": 60,
}


import pytest

pytestmark = pytest.mark.unit

def test_time_in_status_boundaries():
    assert calculate_attendance_status("07:44:00", "time_in", SETTINGS) == "Early"
    assert calculate_attendance_status("07:45:00", "time_in", SETTINGS) == "Present"
    assert calculate_attendance_status("08:15:00", "time_in", SETTINGS) == "Present"
    assert calculate_attendance_status("08:16:00", "time_in", SETTINGS) == "Late"
    assert calculate_attendance_status("09:01:00", "time_in", SETTINGS) == "Absent"


def test_time_out_status_boundaries():
    assert calculate_attendance_status("16:44:00", "time_out", SETTINGS) == "Early"
    assert calculate_attendance_status("16:45:00", "time_out", SETTINGS) == "Out"


def test_zero_absent_threshold_keeps_late_status():
    settings = {**SETTINGS, "absent_threshold_minutes": 0}
    assert calculate_attendance_status("09:00:00", "time_in", settings) == "Late"

def test_half_day_schedule_is_used_for_time_out():
    settings = dict(SETTINGS)
    settings["school_calendar"] = {
        "2026-09-20": {
            "type": "half_day",
            "label": "Half day",
            "time_in": "08:00",
            "time_out": "12:00",
        }
    }
    assert calculate_attendance_status("12:00:00", "time_out", settings, "2026-09-20") == "Out"
    assert calculate_attendance_status("11:44:00", "time_out", settings, "2026-09-20") == "Early"


def test_invalid_half_day_schedule_is_rejected():
    from core import attendance_calendar
    settings = {}
    try:
        attendance_calendar.set_entry(
            settings, "2026-09-20", "half_day", "Bad", "12:00", "08:00"
        )
    except ValueError:
        return
    raise AssertionError("Expected invalid half-day time ordering to be rejected")
