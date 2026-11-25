"""Regression tests for permission hardening, SQL aggregation, backup pruning, and thread safety."""

import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from core import database as db
from core import permissions
from core.attendance import AttendanceProcessor
from gui_web import api as api_module


pytestmark = pytest.mark.unit


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    db_path = tmp_path / "attendance.db"
    monkeypatch.setattr(db, "DB_PATH", str(db_path))
    permissions.set_session_role("admin", 600.0)
    db.init_database()
    yield db_path
    permissions.set_session_role("guest", 600.0)


@pytest.mark.parametrize("role", ["guest", "teacher"])
def test_clear_all_students_and_attendance_require_wipe_permission(isolated_db, role):
    assert db.add_student(1, "S-001", "Alice", "12", "CSS")[0]
    db.log_attendance(1, 200, "GOOD MATCH", datetime(2026, 10, 15, 8, 0, 0))

    permissions.set_session_role(role, 600.0)
    with pytest.raises(PermissionError):
        db.clear_all_students()
    with pytest.raises(PermissionError):
        db.clear_all_attendance()

    assert db.get_student_count() == 1
    assert db.count_attendance_by_date("2026-10-15") == 1


def test_clear_all_attendance_succeeds_for_admin(isolated_db):
    assert db.add_student(1, "S-001", "Alice", "12", "CSS")[0]
    db.log_attendance(1, 200, "GOOD MATCH", datetime(2026, 10, 15, 8, 0, 0))

    permissions.set_session_role("admin", 600.0)
    cleared = db.clear_all_attendance()

    assert cleared == 1
    assert db.count_attendance_by_date("2026-10-15") == 0
    assert db.get_student_count() == 1


def test_sql_statistics_summary_matches_expected_report_counts(isolated_db, monkeypatch):
    assert db.add_student(1, "S-001", "Alice", "12", "CSS")[0]
    assert db.add_student(2, "S-002", "Bob", "12", "STEM")[0]

    # Weak match and unknown scan should not count toward qualified attendance days.
    db.log_attendance(1, 70, "WEAK MATCH", datetime(2026, 10, 14, 8, 0, 0))
    db.log_attendance(0, 0, "UNKNOWN", datetime(2026, 10, 14, 8, 2, 0))
    # Two qualifying scans on the same day count as one attendance day for Alice.
    db.log_attendance(1, 210, "GOOD MATCH", datetime(2026, 10, 15, 8, 0, 0))
    db.log_attendance(1, 220, "GOOD MATCH", datetime(2026, 10, 15, 9, 0, 0))

    api = api_module.Api.__new__(api_module.Api)
    api.serial = type("StubSerial", (), {"is_connected": staticmethod(lambda: False)})()
    monkeypatch.setattr(permissions, "has_permission", lambda action: True)

    report = api.get_statistics_report()

    assert report["total_students"] == 2
    assert report["total_records"] == 1
    assert report["avg_per_student"] == 0.5
    assert report["recent_attendance"] == [{"date": "2026-10-15", "count": 1}]
    assert report["attendance_timeline"] == [{"date": "2026-10-15", "count": 1}]
    assert report["attendance_by_grade"] == [{"grade": "12", "count": 1}]
    assert [row["student_name"] for row in report["all_students"]] == ["Alice", "Bob"]
    assert [row["count"] for row in report["all_students"]] == [1, 0]
    assert report["connected"] is False


def test_get_latest_attendance_for_student_date_returns_newest_row(isolated_db):
    assert db.add_student(3, "S-003", "Carol", "11", "ABM")[0]
    db.log_attendance(3, 210, "GOOD MATCH", datetime(2026, 10, 15, 7, 55, 0))
    db.log_attendance(3, 225, "GOOD MATCH", datetime(2026, 10, 15, 8, 15, 0))

    latest = db.get_latest_attendance_for_student_date(3, "2026-10-15")
    assert latest is not None
    assert latest["time"] == "08:15:00"
    assert latest["event_type"] == "scan"


def test_auto_backup_prunes_stale_backups_but_keeps_pre_restore_snapshots(isolated_db):
    backup_dir = isolated_db.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    old_names = [
        "attendance_20260101_000001.db",
        "attendance_20260101_000002.db",
        "attendance_20260101_000003.db",
    ]
    base_time = time.time() - 7200
    for idx, name in enumerate(old_names):
        path = backup_dir / name
        path.write_bytes(b"SQLite format 3\x00")
        os.utime(path, (base_time + idx * 60, base_time + idx * 60))

    safety_snapshot = backup_dir / "pre_restore_20260101_000000_1.db"
    safety_snapshot.write_bytes(b"SQLite format 3\x00")
    os.utime(safety_snapshot, (base_time - 600, base_time - 600))

    created = db.auto_backup_if_needed(min_interval_hours=0.0, max_backups=2)

    assert created is not None
    remaining_auto = sorted(p.name for p in backup_dir.glob("attendance_*.db"))
    assert len(remaining_auto) == 2
    assert Path(created).name in remaining_auto
    assert safety_snapshot.exists()


def test_role_permissions_normalizes_administrator_label():
    api = api_module.Api.__new__(api_module.Api)
    assert api.get_role_permissions("Administrator") == api.get_role_permissions("admin")
    assert "wipe" in api.get_role_permissions("Administrator")


def test_permissions_session_access_is_thread_safe():
    errors = []

    def worker(role):
        try:
            for _ in range(100):
                permissions.set_session_role(role, 60.0)
                permissions.touch_session()
                current = permissions.get_current_role()
                assert current in {"guest", "teacher", "admin"}
        except BaseException as exc:
            errors.append(exc)

    threads = [
        threading.Thread(target=worker, args=(role,))
        for role in ("guest", "teacher", "admin")
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    assert not errors
    permissions.set_session_role("guest", 600.0)


def test_attendance_processor_handles_legacy_and_json_matches_consistently():
    logged = []
    processor = AttendanceProcessor(
        cooldown_seconds=60,
        min_confidence=150,
        log_attendance_fn=lambda fid, conf, status, now: logged.append((fid, conf, status)),
    )

    weak_json = processor.process_line('{"type":"attendance","event":"match","id":5,"confidence":100}')
    assert weak_json is not None
    assert weak_json["status"] == "WEAK MATCH"
    assert weak_json["logged"] is False

    processor.process_line("ID:5")
    good_legacy = processor.process_line("CONFIDENCE:180")
    assert good_legacy is not None
    assert good_legacy["status"] == "GOOD MATCH"
    assert good_legacy["logged"] is True
    assert logged == [(5, 180, "GOOD MATCH")]
