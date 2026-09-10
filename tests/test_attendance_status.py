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


def test_time_in_status_boundaries():
    assert calculate_attendance_status("07:44:00", "time_in", SETTINGS) == "Early"
    assert calculate_attendance_status("07:45:00", "time_in", SETTINGS) == "Present"
    assert calculate_attendance_status("08:15:00", "time_in", SETTINGS) == "Present"
    assert calculate_attendance_status("08:16:00", "time_in", SETTINGS) == "Late"
    assert calculate_attendance_status("09:01:00", "time_in", SETTINGS) == "Absent"


def test_time_out_status_boundaries():
    assert calculate_attendance_status("16:44:00", "time_out", SETTINGS) == "Early"
    assert calculate_attendance_status("16:45:00", "time_out", SETTINGS) == "Present"


def test_zero_absent_threshold_keeps_late_status():
    settings = {**SETTINGS, "absent_threshold_minutes": 0}
    assert calculate_attendance_status("09:00:00", "time_in", settings) == "Late"