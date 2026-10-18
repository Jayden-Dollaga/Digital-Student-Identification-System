from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from core.database import export_attendance_rows_with_time_in_out


import pytest

pytestmark = pytest.mark.unit

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
        {**base, "time": "17:00:00", "confidence": 0, "status": "TIME OUT", "event_type": "time_out"},
    ])

    assert rows[0]["time_in"] == "08:00:00"
    assert rows[0]["time_out"] == "17:00:00"


def test_export_weak_match_does_not_populate_time_in_or_time_out():
    rows = export_attendance_rows_with_time_in_out([{
        "student_no": "LRN-001",
        "student_name": "Alex Reyes",
        "grade": "12",
        "section": "CSS",
        "date": "2026-09-11",
        "time": "08:00:00",
        "confidence": 80,
        "status": "WEAK MATCH",
        "event_type": "time_in",
    }])

    assert len(rows) == 1
    assert rows[0]["time_in"] == ""
    assert rows[0]["time_out"] == ""
    assert rows[0]["status"] == "WEAK MATCH"


def test_export_good_match_overrides_earlier_weak_match():
    base = {
        "student_no": "LRN-001",
        "student_name": "Alex Reyes",
        "grade": "12",
        "section": "CSS",
        "date": "2026-09-11",
    }
    rows = export_attendance_rows_with_time_in_out([
        {**base, "time": "07:59:00", "confidence": 80, "status": "WEAK MATCH", "event_type": "time_in"},
        {**base, "time": "08:04:00", "confidence": 210, "status": "GOOD MATCH", "event_type": "time_out"},
    ])

    assert len(rows) == 1
    assert rows[0]["time_in"] == "08:04:00"
    assert rows[0]["time_out"] == ""
    assert rows[0]["status"] == "GOOD MATCH"
    assert rows[0]["confidence"] == 210

def test_export_legacy_second_scan_does_not_become_time_out():
    base = {
        "student_no": "LRN-002",
        "student_name": "Sam Lee",
        "grade": "12",
        "section": "CSS",
        "date": "2026-09-11",
        "confidence": 200,
        "status": "GOOD MATCH",
    }
    rows = export_attendance_rows_with_time_in_out([
        {**base, "time": "08:00:00", "event_type": "time_in"},
        {**base, "time": "12:00:00", "event_type": "time_out"},
    ])

    assert rows[0]["time_in"] == "08:00:00"
    assert rows[0]["time_out"] == ""

