"""Regression tests: atomic Time In classification and cached time parsing."""

import sqlite3
import sys
import threading
from datetime import datetime, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from core import attendance_status, database

pytestmark = pytest.mark.unit

STUDENT_COUNT = 24


def _letters(number: int) -> str:
    """Student names may not contain digits, so spell the number with letters."""
    return "".join(chr(ord("a") + int(digit)) for digit in str(number))


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "attendance.db"))
    database.init_database()
    for fingerprint_id in range(1, STUDENT_COUNT + 1):
        ok, message = database.add_student(
            fingerprint_id, f"S-{fingerprint_id:03d}", f"Name {_letters(fingerprint_id)}", "12", "A"
        )
        assert ok, message
    return tmp_path / "attendance.db"


def test_simultaneous_scans_record_exactly_one_time_in(isolated_db):
    """A fingerprint and an RFID scan at the same instant must not both be Time In."""
    base = datetime(2026, 10, 19, 7, 0, 0)
    barrier = threading.Barrier(2)
    errors = []

    def scan(fingerprint_id: int, offset: int) -> None:
        try:
            barrier.wait(timeout=10)
            database.log_attendance(fingerprint_id, 200, "PRESENT", base + timedelta(seconds=offset))
        except Exception as exc:  # surfaced below so a failure is not silent
            errors.append(exc)

    for fingerprint_id in range(1, STUDENT_COUNT + 1):
        threads = [threading.Thread(target=scan, args=(fingerprint_id, offset)) for offset in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)
        barrier.reset()

    assert not errors

    with sqlite3.connect(isolated_db) as conn:
        duplicate_days = conn.execute(
            "SELECT COUNT(*) FROM (SELECT 1 FROM attendance WHERE event_type = 'time_in' "
            "GROUP BY fingerprint_id, date HAVING COUNT(*) > 1)"
        ).fetchone()[0]
        total_rows = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
        time_ins = conn.execute(
            "SELECT COUNT(*) FROM attendance WHERE event_type = 'time_in'"
        ).fetchone()[0]

    assert duplicate_days == 0
    assert total_rows == STUDENT_COUNT * 2  # every scan is kept in the audit trail
    assert time_ins == STUDENT_COUNT  # but exactly one per student per day is Time In


def test_repeated_scans_keep_first_scan_as_time_in(isolated_db):
    base = datetime(2026, 10, 19, 7, 55, 0)
    for minute in range(4):
        database.log_attendance(1, 200, "PRESENT", base + timedelta(minutes=minute))

    summary = [r for r in database.get_daily_attendance_summary("2026-10-19", "2026-10-19") if r["student_no"] == "S-001"]

    assert len(summary) == 1
    assert summary[0]["time_in"] == "07:55:00"
    assert summary[0]["time_out"] == ""


@pytest.mark.parametrize("bad_value", ["", "abc", "24:00", "08:60", None])
def test_cached_minutes_still_rejects_invalid_values_every_time(bad_value):
    """Errors must not be cached as results: the second call must raise too."""
    for _ in range(3):
        with pytest.raises((ValueError, TypeError)):
            attendance_status._minutes(bad_value)


def test_cached_minutes_values_are_correct_for_every_minute_of_the_day():
    for hour in range(24):
        for minute in range(60):
            assert attendance_status._minutes(f"{hour:02d}:{minute:02d}") == hour * 60 + minute
