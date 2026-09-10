from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from core.database import export_attendance_rows_with_time_in_out


def test_export_rows_leave_time_out_empty_for_single_time_in():
    rows = export_attendance_rows_with_time_in_out([{
        "student_no": "123456789012",
        "student_name": "José",
        "grade": "12",
        "section": "A",
        "date": "2026-09-11",
        "time": "08:00:00",
        "confidence": 200,
        "status": "GOOD MATCH",
        "event_type": "time_in",
    }])

    assert rows[0]["time_in"] == "08:00:00"
    assert rows[0]["time_out"] == ""


def test_export_rows_separate_time_in_and_time_out():
    base = {
        "student_no": "123456789012",
        "student_name": "José",
        "grade": "12",
        "section": "A",
        "date": "2026-09-11",
        "confidence": 200,
        "status": "GOOD MATCH",
    }
    rows = export_attendance_rows_with_time_in_out([
        {**base, "time": "08:00:00", "event_type": "time_in"},
        {**base, "time": "17:00:00", "event_type": "time_out"},
    ])

    assert rows[0]["time_in"] == "08:00:00"
    assert rows[0]["time_out"] == "17:00:00"