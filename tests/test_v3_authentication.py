import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from core import auth, permissions
from gui_web import api as api_module


def test_password_hash_is_salted_and_verifies():
    first = auth.hash_password("correct horse battery")
    second = auth.hash_password("correct horse battery")

    assert first["password_salt"] != second["password_salt"]
    assert auth.verify_password("correct horse battery", first)
    assert not auth.verify_password("wrong password", first)
    assert "correct horse battery" not in str(first)


def test_role_hierarchy_is_ordered():
    assert permissions.has_role_permission("admin", "teacher")
    assert permissions.has_role_permission("teacher", "guest")
    assert not permissions.has_role_permission("teacher", "admin")
    assert not permissions.has_role_permission("unknown", "guest")


def test_api_starts_guest_and_requires_password_for_elevation(monkeypatch):
    record = auth.hash_password("dsis-admin")
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

    authenticated = instance.authenticate_role("admin", "dsis-admin")
    assert authenticated["ok"] is True
    assert authenticated["role"] == "admin"


def test_non_admin_role_switches_are_immediate():
    instance = api_module.Api.__new__(api_module.Api)
    instance._session_timeout_seconds = 600.0
    permissions.set_session_role("guest", 600.0)

    teacher = instance.set_current_role("teacher")
    assert teacher["ok"] is True
    assert teacher["role"] == "teacher"

    guest = instance.set_current_role("guest")
    assert guest["ok"] is True
    assert guest["role"] == "guest"


def test_teacher_to_admin_requires_password_without_changing_role():
    instance = api_module.Api.__new__(api_module.Api)
    instance._session_timeout_seconds = 600.0
    permissions.set_session_role("teacher", 600.0)

    result = instance.set_current_role("admin")

    assert result["ok"] is False
    assert result["requires_password"] is True
    assert instance.get_current_role() == "teacher"


def test_wrong_password_does_not_elevate(monkeypatch):
    settings = {"auth": auth.hash_password("dsis-admin")}
    monkeypatch.setattr(api_module, "load_settings", lambda: dict(settings))

    instance = api_module.Api.__new__(api_module.Api)
    instance._session_timeout_seconds = 600.0
    permissions.set_session_role("guest", 600.0)

    result = instance.authenticate_role("admin", "incorrect")
    assert result["ok"] is False
    assert instance.get_current_role() == "guest"


def test_lock_and_expiry_return_to_guest(monkeypatch):
    settings = {"auth": auth.hash_password("dsis-admin")}
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
