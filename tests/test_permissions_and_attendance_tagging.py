"""Tests for backend permission enforcement and Time-In/Time-Out tagging.

Covers three fixes:
  1. core.commands now enforces role permissions (not just the Qt UI).
  2. attendance rows are tagged with event_type ('time_in'/'time_out') at
     insert time instead of it being inferred later from row order.
  3. get_today_attendance_info() reports whether it fell back to recent
     records because there were none for today.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from core import database as db_module
from core.commands import cmd_enroll, cmd_delete, cmd_wipe
from core import permissions as permissions_module


@pytest.fixture()
def temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "attendance_test.db"
    monkeypatch.setattr(db_module, "DB_PATH", str(db_path))
    db_module.init_database()
    return db_path


class TestBackendPermissionEnforcement:
    def test_guest_cannot_enroll(self, monkeypatch):
        monkeypatch.setattr(permissions_module, "get_current_role", lambda: "guest")
        handler = MagicMock()
        handler.send_command.return_value = True

        result = cmd_enroll(handler)

        assert result is False
        handler.send_command.assert_not_called()

    def test_guest_cannot_delete(self, monkeypatch):
        monkeypatch.setattr(permissions_module, "get_current_role", lambda: "guest")
        handler = MagicMock()
        handler.send_command.return_value = True

        result = cmd_delete(handler, 5)

        assert result is False
        handler.send_command.assert_not_called()

    def test_teacher_cannot_wipe(self, monkeypatch):
        monkeypatch.setattr(permissions_module, "get_current_role", lambda: "teacher")
        handler = MagicMock()
        handler.send_command.return_value = True

        result = cmd_wipe(handler)

        assert result is False
        handler.send_command.assert_not_called()

    def test_admin_can_wipe(self, monkeypatch):
        monkeypatch.setattr(permissions_module, "get_current_role", lambda: "admin")
        handler = MagicMock()
        handler.send_command.return_value = True

        result = cmd_wipe(handler)

        assert result is True
        handler.send_command.assert_called_once_with("WIPE")

    def test_unknown_role_is_denied_not_allowed(self, monkeypatch):
        """Fail closed: an unrecognized role must not grant access."""
        monkeypatch.setattr(permissions_module, "get_current_role", lambda: "totally-made-up-role")
        handler = MagicMock()

        assert cmd_wipe(handler) is False
        handler.send_command.assert_not_called()

    def test_disconnect_cancels_active_device_state_before_closing_port(self, monkeypatch):
        from gui_web.api import Api

        api = Api()
        api.serial.is_connected = MagicMock(return_value=True)
        api.serial.disconnect = MagicMock()
        api._scanning = True
        api._pending_enroll = True
        api._pending_wipe = True
        api._pending_delete_id = 7
        stop_mock = MagicMock(return_value=True)
        monkeypatch.setattr("gui_web.api.cmds.cmd_stop", stop_mock)

        api.disconnect()

        assert api._scanning is False
        assert api._pending_enroll is False
        assert api._pending_wipe is False
        assert api._pending_delete_id is None
        stop_mock.assert_called_once_with(api.serial)
        api.serial.disconnect.assert_called_once()

    def test_scan_state_machine_updates_mode_and_scanning_flags(self, monkeypatch):
        from gui_web.api import Api

        api = Api()
        api.serial.is_connected = MagicMock(return_value=True)
        api._push = MagicMock()
        monkeypatch.setattr("gui_web.api.permissions.require_permission", lambda action: True)
        monkeypatch.setattr("gui_web.api.cmds.cmd_scan", lambda handler: True)
        monkeypatch.setattr("gui_web.api.cmds.cmd_stop", lambda handler: True)

        assert api.start_scan() is True
        assert api._scanning is True
        assert api._device_mode == "scan"

        api.stop_scan()
        assert api._scanning is False
        assert api._device_mode == "command"

    def test_unexpected_disconnect_clears_pending_operations_and_publishes_state(self):
        from gui_web.api import Api

        api = Api()
        api.serial.is_connected = MagicMock(return_value=False)
        api._observed_connected = True
        api._scanning = True
        api._device_mode = "scan"
        api._pending_enroll = True
        api._pending_delete_id = 9
        api._pending_wipe = True
        api._push = MagicMock()

        assert api._sync_connection_state() is False

        assert api._scanning is False
        assert api._device_mode == "command"
        assert api._pending_enroll is False
        assert api._pending_delete_id is None
        assert api._pending_wipe is False
        api._push.assert_any_call("connection_status", api.get_connection_status())
        api._push.assert_any_call("connection_changed", {"connected": False})

    def test_device_operations_are_mutually_exclusive(self, monkeypatch):
        from gui_web.api import Api

        api = Api()
        api.serial.is_connected = MagicMock(return_value=True)
        api._pending_enroll = True
        api._push = MagicMock()
        monkeypatch.setattr("gui_web.api.permissions.require_permission", lambda action: True)
        send_mock = MagicMock(return_value=True)
        monkeypatch.setattr("gui_web.api.cmds.cmd_wipe", send_mock)

        result = api.wipe_all_on_device()

        assert result["ok"] is False
        assert "enrollment" in result["message"].lower()
        send_mock.assert_not_called()

    def test_connect_honors_explicit_auto_detect_setting(self, monkeypatch):
        from gui_web.api import Api

        api = Api()
        api.serial.connect = MagicMock(return_value=(False, "not found"))
        monkeypatch.setattr(api, "_start_read_loop", MagicMock())

        result = api.connect(port="", baud=115200, auto_detect=False)

        assert result["connected"] is False
        api.serial.connect.assert_called_once_with(port="", baud=115200, auto_detect=False)

    def test_guest_cannot_list_backups(self, monkeypatch):
        from gui_web.api import Api

        api = Api()
        monkeypatch.setattr("gui_web.api.permissions.require_permission", lambda action: False)
        list_mock = MagicMock(return_value=[{"name": "secret.zip"}])
        monkeypatch.setattr("gui_web.api.db.list_backups", list_mock)

        assert api.list_backups() == []
        list_mock.assert_not_called()

    def test_guest_cannot_generate_statistics_report(self, monkeypatch):
        from gui_web.api import Api

        api = Api()
        monkeypatch.setattr("gui_web.api.permissions.has_permission", lambda action: False)

        result = api.get_statistics_report()

        assert result["ok"] is False
        assert "report permission" in result["message"]

    def test_enrollment_instructions_are_pushed_as_step_events(self):
        from gui_web.api import Api

        api = Api()
        api._pending_enroll = True
        api._push = MagicMock()

        api._parse_enroll_progress("Step 1: Place finger on sensor...")
        api._parse_enroll_progress("Step 2: Remove finger...")
        api._parse_enroll_progress("Step 3: Place the SAME finger again...")

        assert [call.args[0] for call in api._push.call_args_list] == [
            "enroll_progress",
            "enroll_progress",
            "enroll_progress",
        ]
        assert api._push.call_args_list[0].args[1]["event"] == "step"
        assert "Place finger" in api._push.call_args_list[0].args[1]["message"]

    def test_discard_enrollment_removes_unsaved_device_template(self, monkeypatch):
        from gui_web.api import Api

        api = Api()
        api.serial.is_connected = MagicMock(return_value=True)
        monkeypatch.setattr("gui_web.api.permissions.require_permission", lambda action: True)
        monkeypatch.setattr("gui_web.api.cmds.cmd_stop", MagicMock(return_value=True))
        delete_mock = MagicMock(return_value=True)
        monkeypatch.setattr("gui_web.api.cmds.cmd_delete", delete_mock)

        result = api.discard_enrollment(22)

        assert result["ok"] is True
        assert api._pending_delete_id == 22
        delete_mock.assert_called_once_with(api.serial, 22)


class TestAttendanceEventTypeTagging:
    def test_first_scan_of_day_is_tagged_time_in(self, temp_db):
        db_module.add_student(1, "S-1", "Student One", "10", "A")
        db_module.log_attendance(fingerprint_id=1, confidence=100, status="Present")

        rows = db_module.get_attendance_by_student(1)
        assert rows[0]["event_type"] == "time_in"

    def test_second_scan_same_day_is_tagged_time_out(self, temp_db):
        db_module.add_student(1, "S-1", "Student One", "10", "A")
        db_module.log_attendance(fingerprint_id=1, confidence=100, status="Present")
        db_module.log_attendance(fingerprint_id=1, confidence=99, status="Present")

        rows = db_module.get_attendance_by_student(1)
        event_types = {row["event_type"] for row in rows}
        assert "time_in" in event_types
        assert "time_out" in event_types

    def test_daily_summary_uses_tagged_time_in_and_out(self, temp_db):
        import datetime

        db_module.add_student(1, "S-1", "Student One", "10", "A")
        morning = datetime.datetime(2026, 8, 14, 7, 30, 0)
        afternoon = datetime.datetime(2026, 8, 14, 16, 0, 0)
        db_module.log_attendance(fingerprint_id=1, confidence=100, status="Present", now=morning)
        db_module.log_attendance(fingerprint_id=1, confidence=98, status="Present", now=afternoon)

        summary = db_module.get_daily_attendance_summary(start_date="2026-08-14", end_date="2026-08-14")
        assert len(summary) == 1
        assert summary[0]["time_in"] == "07:30:00"
        assert summary[0]["time_out"] == "16:00:00"

    def test_migration_backfills_legacy_rows_without_event_type(self, temp_db):
        """Rows inserted before the event_type column existed should get
        backfilled the next time init_database() runs."""
        with db_module.get_connection() as conn:
            conn.execute(
                "INSERT INTO students (fingerprint_id, student_no, student_name, grade, section, "
                "enrollment_date, updated_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (1, "S-1", "Student One", "10", "A", "2026-08-01T00:00:00", "2026-08-01T00:00:00"),
            )
            conn.execute(
                "INSERT INTO attendance (fingerprint_id, date, time, confidence, status, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (1, "2026-08-14", "07:00:00", 100, "Present", "2026-08-14T07:00:00"),
            )
            conn.execute(
                "INSERT INTO attendance (fingerprint_id, date, time, confidence, status, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (1, "2026-08-14", "16:00:00", 100, "Present", "2026-08-14T16:00:00"),
            )
            conn.commit()

        # Re-running init_database triggers the backfill migration.
        db_module.init_database()

        rows = db_module.get_attendance_by_student(1)
        rows_by_time = {row["time"]: row["event_type"] for row in rows}
        assert rows_by_time["07:00:00"] == "time_in"
        assert rows_by_time["16:00:00"] == "time_out"


class TestTodayAttendanceFallbackFlag:
    def test_is_fallback_false_when_todays_records_exist(self, temp_db):
        db_module.add_student(1, "S-1", "Student One", "10", "A")
        db_module.log_attendance(fingerprint_id=1, confidence=100, status="Present")

        info = db_module.get_today_attendance_info()

        assert info["is_fallback"] is False
        assert len(info["rows"]) == 1

    def test_is_fallback_true_when_only_older_records_exist(self, temp_db):
        import datetime

        db_module.add_student(1, "S-1", "Student One", "10", "A")
        last_week = datetime.datetime.now() - datetime.timedelta(days=7)
        db_module.log_attendance(fingerprint_id=1, confidence=100, status="Present", now=last_week)

        info = db_module.get_today_attendance_info()

        assert info["is_fallback"] is True
        assert len(info["rows"]) == 1

    def test_get_attendance_today_still_returns_plain_list(self, temp_db):
        """Backward compatibility: existing callers expect a list, not a dict."""
        db_module.add_student(1, "S-1", "Student One", "10", "A")
        db_module.log_attendance(fingerprint_id=1, confidence=100, status="Present")

        rows = db_module.get_attendance_today()

        assert isinstance(rows, list)
        assert len(rows) == 1
