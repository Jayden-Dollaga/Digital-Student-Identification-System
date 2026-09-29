from pathlib import Path

import pytest

from run_web_gui import main as launch_application
from startup_preflight import PreflightReport
from startup_preflight import check_startup_preflight


def _check(tmp_path, **overrides):
    inputs = {
        "version_info": (3, 12, 0),
        "import_module": lambda name: object(),
        "port_lister": lambda: ["COM4"],
        "database_path": tmp_path / "data" / "attendance.db",
        "is_windows": True,
        "webview2_available": True,
    }
    inputs.update(overrides)
    result = check_startup_preflight(**inputs)
    assert result is not None, "preflight returned no result"
    return result


@pytest.mark.parametrize("version_info", [(3, 10, 9), (3, 15, 0)])
def test_unsupported_python_version_is_a_hard_failure(tmp_path, version_info):
    result = _check(tmp_path, version_info=version_info)

    assert result.ok is False
    assert any("Python" in message and "3.11" in message and "3.14" in message for message in result.errors)


def test_missing_runtime_package_is_a_hard_failure(tmp_path):
    imported = []

    def import_module(name):
        imported.append(name)
        if name == "serial":
            raise ModuleNotFoundError("No module named 'serial'")
        return object()

    result = _check(tmp_path, import_module=import_module)

    assert result.ok is False
    assert any("pyserial" in message for message in result.errors)
    assert any("install_requirements.bat" in message for message in result.errors)
    assert not any("PySide6" in message or "pytest" in message for message in result.errors)
    assert not {"customtkinter", "PySide6", "pytest", "pytest_forked", "PyInstaller"}.intersection(imported)


def test_missing_windows_webview2_is_a_hard_failure(tmp_path):
    result = _check(tmp_path, webview2_available=False)

    assert result.ok is False
    assert any("WebView2" in message for message in result.errors)


def test_unwritable_database_path_is_a_hard_failure(tmp_path):
    path_blocker = tmp_path / "not-a-directory"
    path_blocker.write_text("blocker", encoding="utf-8")

    result = _check(tmp_path, database_path=path_blocker / "attendance.db")

    assert result.ok is False
    assert any("database" in message.lower() and "writ" in message.lower() for message in result.errors)


def test_no_serial_ports_is_warning_only_with_driver_hint(tmp_path):
    result = _check(tmp_path, port_lister=lambda: [])

    assert result.ok is True
    assert not result.errors
    assert any("WARNING" in message and "serial" in message.lower() for message in result.warnings)
    assert any("CH340" in message and "CP210x" in message for message in result.warnings)


def test_serial_port_permission_error_is_warning_only(tmp_path):
    def port_lister():
        raise PermissionError("Access is denied")

    result = _check(tmp_path, port_lister=port_lister)

    assert result.ok is True
    assert not result.errors
    assert any("permission" in message.lower() for message in result.warnings)


def test_serial_port_busy_is_warning_only(tmp_path):
    def port_lister():
        raise OSError("device is busy")

    result = _check(tmp_path, port_lister=port_lister)

    assert result.ok is True
    assert not result.errors
    assert any("busy" in message.lower() for message in result.warnings)


def test_all_preflight_checks_pass_without_messages(tmp_path):
    result = _check(tmp_path)

    assert result.ok is True
    assert not result.errors
    assert not result.warnings


def test_launcher_prints_hard_failure_and_exits_before_opening_app(capsys):
    launched = []
    report = PreflightReport(("Missing package: pywebview",), ())

    with pytest.raises(SystemExit) as exit_info:
        launch_application(lambda: report, lambda: launched.append(True))

    assert exit_info.value.code == 1
    assert "ERROR: Missing package: pywebview" in capsys.readouterr().err
    assert not launched


def test_launcher_prints_warning_and_continues_startup(capsys):
    launched = []
    report = PreflightReport((), ("WARNING: No serial port was detected.",))

    launch_application(lambda: report, lambda: launched.append(True))

    assert "WARNING: No serial port was detected." in capsys.readouterr().err
    assert launched == [True]