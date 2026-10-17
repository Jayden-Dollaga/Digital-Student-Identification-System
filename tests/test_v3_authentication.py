import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from core import auth, permissions
from gui_web import api as api_module


import pytest

pytestmark = pytest.mark.unit

def test_attendance_evaluation_export_requires_export_permission(monkeypatch):
    instance = api_module.Api.__new__(api_module.Api)
    monkeypatch.setattr(api_module.permissions, "require_permission", lambda action: False)
    monkeypatch.setattr(
        instance,
        "get_attendance_evaluation",
        lambda *args, **kwargs: pytest.fail("Report must not be generated without export permission"),
    )

    result = instance.export_attendance_evaluation_csv()

    assert result["ok"] is False
    assert "export permission" in result["message"].lower()


def test_student_field_validation_requires_enrollment_permission(monkeypatch):
    instance = api_module.Api.__new__(api_module.Api)
    monkeypatch.setattr(api_module.permissions, "require_permission", lambda action: False)
    monkeypatch.setattr(
        api_module.db,
        "get_student_field_feedback",
        lambda *args, **kwargs: pytest.fail("Validation must not query roster without enroll permission"),
    )

    result = instance.validate_student_fields("LRN001", "A Student", "12", "CSS")

    assert result["ok"] is False
    assert result["status"] == 403
    assert result["fields"] == {}


def test_api_fails_startup_when_database_initialization_fails(monkeypatch):
    monkeypatch.setattr(
        api_module.db,
        "init_database",
        lambda: (_ for _ in ()).throw(OSError("database unavailable")),
    )

    with pytest.raises(RuntimeError, match="could not initialize its local database"):
        api_module.Api()


def test_application_logs_and_log_folder_are_admin_only(monkeypatch):
    instance = api_module.Api.__new__(api_module.Api)
    permissions.set_session_role("guest", 600.0)
    monkeypatch.setattr(
        api_module.os,
        "startfile",
        lambda path: pytest.fail("Guest must not open the application log folder"),
        raising=False,
    )

    assert instance.get_app_log() == []
    denied = instance.open_log_folder()
    assert denied["ok"] is False
    assert denied["status"] == 403

    permissions.set_session_role("teacher", 600.0)
    assert instance.get_app_log() == []
    assert instance.open_log_folder()["status"] == 403


def test_statistics_report_requires_record_read_permission(monkeypatch):
    instance = api_module.Api.__new__(api_module.Api)
    monkeypatch.setattr(api_module.permissions, "has_permission", lambda action: action == "export")
    monkeypatch.setattr(
        api_module.db,
        "get_attendance_all",
        lambda: pytest.fail("Identifiable attendance must not be read without read_records"),
    )

    result = instance.get_statistics_report()

    assert result["ok"] is False
    assert "record-reading" in result["message"].lower()


def test_password_hash_is_salted_and_verifies():
    first = auth.hash_password("correct horse battery")
    second = auth.hash_password("correct horse battery")

    assert first["password_salt"] != second["password_salt"]
    assert auth.verify_password("correct horse battery", first)
    assert not auth.verify_password("wrong password", first)
    assert "correct horse battery" not in str(first)


def test_password_verification_rejects_malformed_or_expensive_records():
    record = auth.hash_password("correct horse battery")
    excessive = dict(record, iterations=10**12)
    bad_salt = dict(record, password_salt="AA==")
    bad_hash = dict(record, password_hash="not-a-real-hash")

    assert not auth.verify_password("correct horse battery", excessive)
    assert not auth.verify_password("correct horse battery", bad_salt)
    assert not auth.verify_password("correct horse battery", bad_hash)
    assert not auth.verify_password(None, record)
    assert not auth.verify_password("x", None)


def test_password_validation_and_verification_reject_excessive_length():
    huge_password = "x" * (auth.MAX_PASSWORD_LENGTH + 1)
    assert auth.validate_new_password(huge_password, huge_password).startswith("Password must be no longer")
    assert not auth.verify_password(huge_password, auth.hash_password("normal pass"))


def test_password_validation_rejects_non_text_inputs():
    assert auth.validate_new_password(123, 123) == "Password fields must be text."


def test_role_hierarchy_is_ordered():
    assert permissions.has_role_permission("admin", "teacher")
    assert permissions.has_role_permission("teacher", "guest")
    assert not permissions.has_role_permission("teacher", "admin")
    assert not permissions.has_role_permission("unknown", "guest")


def test_default_role_permissions_match_the_session_policy():
    roles = api_module.CONFIG.user_roles

    assert roles["guest"]["permissions"] == ["scan"]
    assert roles["teacher"]["permissions"] == [
        "scan",
        "read_records",
        "export",
        "backup",
        "attendance_evaluation",
    ]


def test_expected_role_permissions_match_documented_policy():
    assert permissions.has_permission("scan", role_key="guest")
    assert not permissions.has_permission("attendance_evaluation", role_key="guest")
    assert not permissions.has_permission("export", role_key="guest")
    assert not permissions.has_permission("backup", role_key="guest")

    assert permissions.has_permission("export", role_key="teacher")
    assert permissions.has_permission("backup", role_key="teacher")
    assert permissions.has_permission("read_records", role_key="teacher")
    assert permissions.has_permission("attendance_evaluation", role_key="teacher")

    assert permissions.has_permission("export", role_key="admin")
    assert permissions.has_permission("backup", role_key="admin")


def test_all_roles_can_access_attendance_evaluation(monkeypatch):
    monkeypatch.setattr(api_module.db, "get_daily_attendance_summary", lambda **kwargs: [])
    monkeypatch.setattr(api_module.db, "get_all_students", lambda: [])
    instance = api_module.Api.__new__(api_module.Api)

    for role in ("admin", "teacher"):
        permissions.set_session_role(role, 600.0)
        assert instance.get_attendance_evaluation()["ok"] is True

    permissions.set_session_role("guest", 600.0)
    assert instance.get_attendance_evaluation()["ok"] is False


def test_api_starts_guest_and_requires_password_for_elevation(monkeypatch):
    record = auth.hash_password("admin")
    settings = {"auth": record}
    monkeypatch.setattr(api_module, "load_settings", lambda: dict(settings))
    monkeypatch.setattr(api_module, "save_settings", lambda value: None)

    instance = api_module.Api.__new__(api_module.Api)
    instance._session_timeout_seconds = 600.0
    permissions.set_session_role("guest", 600.0)

    assert instance.get_current_role() == "guest"
    denied = instance.set_current_role("admin")
    assert denied["ok"] is False
    assert denied["requires_password"] is True

    authenticated = instance.authenticate_role("admin", "admin")
    assert authenticated["ok"] is True
    assert authenticated["role"] == "admin"


def test_guest_cannot_switch_to_teacher_without_admin_session():
    instance = api_module.Api.__new__(api_module.Api)
    instance._session_timeout_seconds = 600.0
    permissions.set_session_role("guest", 600.0)

    teacher = instance.set_current_role("teacher")
    assert teacher["ok"] is False
    assert teacher["requires_password"] is True
    assert instance.get_current_role() == "guest"

    guest = instance.set_current_role("guest")
    assert guest["ok"] is True
    assert guest["role"] == "guest"


def test_export_and_backup_api_methods_allow_teacher_and_admin(monkeypatch, tmp_path):
    instance = api_module.Api.__new__(api_module.Api)
    instance._session_timeout_seconds = 600.0
    permissions.set_session_role("teacher", 600.0)

    assert instance.export_attendance_csv()["message"] != "Current role does not have export permission."
    assert instance.export_students_csv()["message"] != "Current role does not have export permission."
    assert instance.export_statistics_report()["message"] != "Current role does not have export permission."
    assert instance.create_backup()["message"] != "Current role does not have backup permission."

    permissions.set_session_role("admin", 600.0)
    monkeypatch.setattr(api_module.db, "export_attendance_range_with_time_in_out", lambda *args, **kwargs: [{
        "student_no": "001",
        "student_name": "Alice",
        "date": "2024-01-01",
        "time_in": "08:00:00",
        "time_out": "10:00:00",
        "match_status": "Present",
    }])
    monkeypatch.setattr(api_module.db, "get_attendance_today", lambda: [{
        "student_no": "001",
        "student_name": "Alice",
        "date": "2024-01-01",
        "time_in": "08:00:00",
        "time_out": "10:00:00",
        "match_status": "Present",
    }])
    monkeypatch.setattr(api_module.db, "get_all_students", lambda: [{
        "student_no": "001",
        "student_name": "Alice",
        "grade": "7",
        "section": "A",
        "fingerprint_id": 1,
    }])
    monkeypatch.setattr(instance, "_choose_csv_path", lambda filename: tmp_path / filename)
    monkeypatch.setattr(instance, "_rows_to_csv", lambda rows, path: {"ok": True, "message": "Exported", "path": str(path)})
    monkeypatch.setattr(api_module.db, "generate_statistics_report", lambda: "report")
    monkeypatch.setattr(api_module.db, "backup_database", lambda: (True, "Backup created.", str(tmp_path / "backup.db")))

    assert instance.export_attendance_csv()["ok"] is True
    assert instance.export_students_csv()["ok"] is True
    assert instance.export_statistics_report()["ok"] is True
    assert instance.create_backup()["ok"] is True


def test_admin_can_switch_down_to_teacher_without_password():
    instance = api_module.Api.__new__(api_module.Api)
    instance._session_timeout_seconds = 600.0
    permissions.set_session_role("admin", 600.0)

    teacher = instance.set_current_role("teacher")
    assert teacher["ok"] is True
    assert teacher["role"] == "teacher"


def test_teacher_can_reselect_current_role():
    instance = api_module.Api.__new__(api_module.Api)
    instance._session_timeout_seconds = 600.0
    permissions.set_session_role("teacher", 600.0)

    result = instance.set_current_role("teacher")

    assert result["ok"] is True
    assert result["role"] == "teacher"


def test_role_aliases_are_canonicalized_and_teacher_stays_teacher():
    instance = api_module.Api.__new__(api_module.Api)
    instance._session_timeout_seconds = 600.0
    permissions.set_session_role("admin", 600.0)

    teacher = instance.set_current_role("Teacher")
    assert teacher["ok"] is True
    assert teacher["role"] == "teacher"

    admin = instance.set_current_role("Administrator")
    assert admin["ok"] is False
    assert admin["requires_password"] is True
    assert instance.get_current_role() == "teacher"


def test_guest_to_administrator_requires_password():
    instance = api_module.Api.__new__(api_module.Api)
    instance._session_timeout_seconds = 600.0
    permissions.set_session_role("guest", 600.0)

    result = instance.set_current_role("Administrator")

    assert result["ok"] is False
    assert result["requires_password"] is True
    assert instance.get_current_role() == "guest"


def test_teacher_to_admin_requires_password_without_changing_role():
    instance = api_module.Api.__new__(api_module.Api)
    instance._session_timeout_seconds = 600.0
    permissions.set_session_role("teacher", 600.0)

    result = instance.set_current_role("admin")

    assert result["ok"] is False
    assert result["requires_password"] is True
    assert instance.get_current_role() == "teacher"


def test_admin_to_admin_does_not_require_password():
    instance = api_module.Api.__new__(api_module.Api)
    instance._session_timeout_seconds = 600.0
    permissions.set_session_role("admin", 600.0)

    result = instance.set_current_role("admin")

    assert result["ok"] is True
    assert result["role"] == "admin"


def test_guest_can_elevate_to_admin_with_correct_password(monkeypatch):
    settings = {"auth": auth.hash_password("admin")}
    monkeypatch.setattr(api_module, "load_settings", lambda: dict(settings))

    instance = api_module.Api.__new__(api_module.Api)
    instance._session_timeout_seconds = 600.0
    permissions.set_session_role("guest", 600.0)

    result = instance.authenticate_role("admin", "admin")
    assert result["ok"] is True
    assert result["role"] == "admin"


def test_wrong_password_does_not_elevate(monkeypatch):
    settings = {"auth": auth.hash_password("admin")}
    monkeypatch.setattr(api_module, "load_settings", lambda: dict(settings))
    monkeypatch.setattr(api_module, "save_settings", lambda value: settings.update(value))

    instance = api_module.Api.__new__(api_module.Api)
    instance._session_timeout_seconds = 600.0
    permissions.set_session_role("guest", 600.0)

    result = instance.authenticate_role("admin", "incorrect")
    assert result["ok"] is False
    assert instance.get_current_role() == "guest"


def test_admin_password_lockout_persists_across_api_restarts(monkeypatch):
    settings = {"auth": auth.hash_password("admin")}
    monkeypatch.setattr(api_module, "load_settings", lambda: dict(settings))
    monkeypatch.setattr(api_module, "save_settings", lambda value: settings.update(value))

    instance = api_module.Api.__new__(api_module.Api)
    instance._session_timeout_seconds = 600.0
    permissions.set_session_role("guest", 600.0)

    for _ in range(api_module.ADMIN_LOGIN_MAX_FAILURES):
        result = instance.authenticate_role("admin", "incorrect")
        assert result["ok"] is False

    assert settings["auth"]["lockout_until_epoch"] > time.time()
    restarted_instance = api_module.Api.__new__(api_module.Api)
    restarted_instance._session_timeout_seconds = 600.0
    locked = restarted_instance.authenticate_role("admin", "admin")
    assert locked["ok"] is False
    assert "locked" in locked["message"].lower()


def test_first_run_recovery_refuses_password_creation_when_marker_exists():
    instance = api_module.Api.__new__(api_module.Api)
    instance._first_run_setup_required = False
    instance._first_run_recovery_required = True

    result = instance.complete_first_run_setup("correct horse", "correct horse")

    assert result["ok"] is False
    assert "recovery" in result["message"].lower()


def test_admin_initialization_marker_round_trip(tmp_path):
    from settings_store import admin_initialization_marker_exists, write_admin_initialization_marker

    marker = tmp_path / ".admin_initialized"
    assert admin_initialization_marker_exists(marker) is False

    write_admin_initialization_marker(marker)

    assert admin_initialization_marker_exists(marker) is True


def test_guest_record_reads_are_restricted(monkeypatch):
    instance = api_module.Api.__new__(api_module.Api)
    permissions.set_session_role("guest", 600.0)
    monkeypatch.setattr(api_module.db, "get_all_students", lambda: [{"student_name": "Alice"}])

    assert instance.get_students() == []
    assert instance.get_student(1) == {}
    assert instance.get_attendance()["rows"] == []
    assert instance.get_recent_activity() == []


def test_lock_and_expiry_return_to_guest(monkeypatch):
    settings = {"auth": auth.hash_password("admin")}
    monkeypatch.setattr(api_module, "load_settings", lambda: dict(settings))

    instance = api_module.Api.__new__(api_module.Api)
    instance._session_timeout_seconds = 60.0
    permissions.set_session_role("admin", 60.0)
    assert instance.lock_session()["role"] == "guest"

    permissions.set_session_role("admin", 0.01)
    import time
    time.sleep(0.03)
    assert instance.get_session_state()["role"] == "guest"


def test_guest_settings_update_is_rejected(monkeypatch):
    instance = api_module.Api.__new__(api_module.Api)
    permissions.set_session_role("guest", 600.0)
    result = instance.save_ui_settings({"cooldown": 1})
    assert result["ok"] is False
    assert result["status"] == 403


def test_get_settings_never_returns_rfid_key_material(monkeypatch):
    instance = api_module.Api.__new__(api_module.Api)
    permissions.set_session_role("guest", 600.0)
    monkeypatch.setattr(api_module, "load_settings", lambda: {
        "auth": {"password_hash": "hash"},
        "rfid_aes_gcm_key": "A1" * 32,
        "rfid_app_key_hex": "B2" * 32,
        "rfid_payload_key": "secret",
    })
    monkeypatch.setattr(api_module, "list_serial_ports", lambda: [])

    settings = instance.get_settings()

    assert "auth" not in settings
    assert "rfid_aes_gcm_key" not in settings
    assert "rfid_app_key_hex" not in settings
    assert "rfid_payload_key" not in settings


def test_guest_cannot_select_an_arbitrary_serial_port(monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import MagicMock

    instance = api_module.Api.__new__(api_module.Api)
    instance.serial = SimpleNamespace(
        is_connected=MagicMock(return_value=False),
        connect=MagicMock(return_value=(True, "OK")),
    )
    monkeypatch.setattr(api_module.permissions, "get_current_role", lambda: "guest")
    monkeypatch.setattr(api_module.permissions, "require_permission", lambda action: True)
    monkeypatch.setattr(api_module, "load_settings", lambda: {"com_port": "COM5", "baud_rate": 115200})

    result = instance.connect(port="COM6", baud=115200, auto_detect=False)

    assert result["connected"] is False
    assert "permission" in result["message"].lower()
    instance.serial.connect.assert_not_called()
