"""Regression tests for attendance-query indexes created by schema initialization."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOT = ROOT / "python"
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from core import database


pytestmark = pytest.mark.integration


def test_attendance_composite_indexes_are_created_for_existing_database(tmp_path, monkeypatch):
    """Startup upgrades an existing database without requiring a manual migration."""
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "dsis-index-test.db"))

    database.init_database()
    conn = database.get_connection()
    try:
        indexes = {row["name"] for row in conn.execute("PRAGMA index_list(attendance)")}
    finally:
        conn.close()

    assert "idx_attendance_timestamp_id" in indexes
    assert "idx_attendance_date_time_timestamp" in indexes
    assert "idx_attendance_student_date_time" in indexes

def test_text_statistics_report_does_not_count_repeat_scans_as_attendance_days(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "dsis-report-test.db"))
    database.init_database()
    conn = database.get_connection()
    try:
        conn.execute(
            "INSERT INTO students (fingerprint_id, student_no, student_name, grade, section, "
            "card_uid, enrollment_date, updated_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (1, "S-001", "Alice", "12", "CSS", None, "2026-09-01", "2026-09-01"),
        )
        events = [
            (1, "2026-09-10", "08:00:00", 220, "GOOD MATCH", "2026-09-10T08:00:00", "time_in"),
            (1, "2026-09-10", "08:00:10", 220, "GOOD MATCH", "2026-09-10T08:00:10", "scan"),
            (1, "2026-09-10", "17:00:00", 0, "TIME OUT", "2026-09-10T17:00:00", "time_out"),
        ]
        conn.executemany(
            "INSERT INTO attendance (fingerprint_id, date, time, confidence, status, timestamp, event_type) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            events,
        )
        conn.commit()
    finally:
        conn.close()

    report = database.generate_statistics_report()
    assert "Total Attendance Days: 1" in report
    assert "Average Attendance Days per Student: 1.0 days" in report
    assert "Alice" in report
