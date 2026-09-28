"""Static and bridge-level smoke checks for the V3 HTML/pywebview UI."""

from pathlib import Path
from datetime import datetime
import json
import sys
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "python" / "gui_web" / "web"
PYTHON_ROOT = ROOT / "python"
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from core import permissions


pytestmark = pytest.mark.integration

def test_v3_web_shell_contains_all_primary_workflows():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    script = (WEB_ROOT / "app.js").read_text(encoding="utf-8")

    for page in ("dashboard", "attendance", "students", "reports", "logs", "settings"):
        assert f'id="page-{page}"' in html
    for workflow in (
        "toggleConnect",
        "toggleScan",
        "startEnrollment",
        "deleteSelectedStudent",
        "deleteSelectedStudents",
        "processBatchDelete",
        "wipeAllFingerprints",
        "restoreBackup",
    ):
        assert f"function {workflow}" in script
    for event in ("connection_status", "mode_changed", "enroll_progress", "delete_progress", "wipe_progress", "data_changed"):
        assert event in script
    assert "<th>Attendance</th>" in html
    assert "Export Weekly Attendance (CSV)" in html
    assert '<option>Recent</option>\n            <option>Today</option>' in html
    assert 'id="export-week"' in html
    assert 'id="export-week-label"' in html
    assert "isoWeekToMonday" in script
    assert "formatWeekRange" in script
    assert "&#9664; Prev" in html
    assert "Next &#9654;" in html
    assert "attendance_status" in script
    assert "attendanceBadgeClass" in script
    assert 'id="stu-select-all"' in html
    assert 'id="stu-delete-selected"' in html
    assert "handleBatchDeleteProgress" in script
    assert "Retry remaining" in script
    assert 'id="sm-reset-btn"' in html
    assert "function resetDevice" in script
    assert "function resetBlockReason" in script
    assert "api().reset_device" in script
    assert "showStatisticsCharts" in script
    assert "renderAttendanceTimeline" in script
    assert "renderSectionChart" in script
    assert "renderAttendanceGradeChart" in script
    assert "statistics-charts-overlay" in script
    assert "showSerialTroubleshooting" in script
    assert "connection_troubleshooting" in script
    assert "serial-troubleshooting-overlay" in script
    assert "Troubleshoot connection" in html
    assert "exportStatisticsReport" in script
    assert "Recent Attendance by Date" in script
    assert "school_weekdays_off" in script
    assert "cal-day-no-class" in script
    assert 'id="stats-connection-summary"' in html
    assert "validate_student_fields" in script
    assert "validateEnrollmentFields" in script
    assert 'id="em-validation-summary"' in script
    assert 'id="em-sno-feedback"' in script
    assert 'id="lock-btn"' not in html
    assert "lockButton.hidden" not in script


def test_unknown_attendance_rows_use_unknown_data_label():
    script = (WEB_ROOT / "app.js").read_text(encoding="utf-8")

    assert "Unknown data" in script
    assert "Unknown fingerprint" not in script
    assert "Unknown RFID card" in script


def test_rfid_registration_waits_for_verified_write_result():
    script = (WEB_ROOT / "app.js").read_text(encoding="utf-8")
    api_source = (ROOT / "python" / "gui_web" / "api.py").read_text(encoding="utf-8")

    assert "payload.method === 'rfid_register'" in script
    assert "payload.event === 'saved'" in script
    assert "bindPendingCardFromScan" not in script
    assert "Write and verify" in script
    assert "payload.card_type" in script
    assert "Verified erase" in script
    assert "Present and hold each card on the reader until the log confirms the erase." in script
    assert "Place a different card on the reader to replace it." in script
    assert "Keep it on the reader while encrypted data is written and verified." in api_source
    assert "second presentation" not in script
    assert "PICC_WakeupA" in (ROOT / "firmware" / "ESP32_DSIS_AllInOne" / "ESP32_DSIS_AllInOne.ino").read_text(encoding="utf-8")
    assert "payload.card_type" in script
    assert "Verified erase" in script


def test_student_refresh_preserves_the_selected_fingerprint():
    script = (WEB_ROOT / "app.js").read_text(encoding="utf-8")

    assert "const previousFingerprintId = selectedStudent ? Number(selectedStudent.fingerprint_id) : null;" in script
    assert "students.find(s => Number(s.fingerprint_id) === previousFingerprintId) || students[0]" in script


def test_scan_shows_popup_when_esp32_is_disconnected():
    script = (WEB_ROOT / "app.js").read_text(encoding="utf-8")

    assert "ESP32 not connected. Connect first to start scanning." in script
    assert "const connection = await api().get_connection_status();" in script
    assert "Could not start scanning. Check that the ESP32 is ready." in script
    assert "Place and hold a finger on the sensor or a card on the RC522 until detected." in script


def test_startup_auto_connect_uses_persisted_delay_and_can_be_disabled():
    script = (WEB_ROOT / "app.js").read_text(encoding="utf-8")
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")

    assert "Reconnect automatically after disconnect" in html
    assert "Connect automatically when the app starts" in html
    assert 'id="set-auto-connect"' in html
    assert 'id="set-startup-connect-delay" type="number" min="0" max="30000" step="100"' in html
    assert "function scheduleStartupAutoConnect(settings)" in script
    assert "if (!settings.auto_connect_on_startup) return;" in script
    assert "Math.max(0, Math.min(30000, configuredDelay))" in script
    assert "toggleConnect({ silent: true, startup: true })" in script
    assert "scheduleStartupAutoConnect(s)" in script
    assert "clearTimeout(startupConnectTimer)" in script


def test_startup_connect_delay_is_clamped_when_settings_are_saved(monkeypatch):
    from gui_web.api import Api
    from settings_store import default_settings

    api = Api()
    captured = {}
    monkeypatch.setattr("gui_web.api.permissions.require_role", lambda role: True)
    monkeypatch.setattr("gui_web.api.load_settings", default_settings)
    monkeypatch.setattr("gui_web.api.save_settings", lambda settings: captured.update(settings))

    for delay, expected in ((-50, 0), (60000, 30000)):
        result = api.save_ui_settings({
            "auto_connect_on_startup": True,
            "startup_connect_delay_ms": delay,
        })
        assert result["ok"] is True
        assert captured["startup_connect_delay_ms"] == expected
        assert captured["auto_connect_on_startup"] is True


def test_restore_defaults_cancels_autosave_then_reloads_all_settings():
    script = (WEB_ROOT / "app.js").read_text(encoding="utf-8")
    start = script.index("async function restoreDefaultSettings()")
    end = script.index("\n}", start)
    restore_function = script[start:end]

    assert restore_function.index("clearTimeout(settingsSaveTimer)") < restore_function.index("api().restore_default_settings()")
    assert "settingsSaveTimer = null" in restore_function
    assert "await loadSettingsPage()" in restore_function
    assert "await loadDashboard()" in restore_function
    assert "Defaults restored" in restore_function


def test_role_auth_password_supports_enter_and_clipboard_paste():
    script = (WEB_ROOT / "app.js").read_text(encoding="utf-8")
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    styles = (WEB_ROOT / "styles.css").read_text(encoding="utf-8")

    assert "event.key === 'Enter' && event.target.id === 'role-auth-password'" in script
    assert 'id="role-auth-password" class="settings-text-input" type="password"' in html
    assert ".settings-text-input {" in styles and "user-select: text;" in styles


def test_batch_rfid_erase_dialog_has_responsive_live_log():
    script = (WEB_ROOT / "app.js").read_text(encoding="utf-8")
    styles = (WEB_ROOT / "styles.css").read_text(encoding="utf-8")

    assert 'aria-label="RFID erase log"' in script
    assert 'id="batch-rfid-log" class="batch-rfid-log" role="log"' in script
    assert "function appendBatchRfidEraseLog(event, message)" in script
    assert "Erase verified:" in script
    assert "Card detected:" in script
    assert "Skipped:" in script
    assert "while (log.children.length > 50)" in script
    assert "batchRfidEraseWaitTimer = setTimeout" in script
    assert "}, 12000);" in script
    assert "second presentation" not in script
    assert "grid-template-columns: minmax(0, 1fr) 240px;" in styles
    assert "@media (max-width: 760px)" in styles


def test_delete_and_wipe_are_blocked_while_scan_is_active():
    script = (WEB_ROOT / "app.js").read_text(encoding="utf-8")

    assert "Scan is active. Stop attendance scanning before ${action}." in script
    workflows = (
        ("async function deleteSelectedStudent()", "async function deleteSelectedStudents()"),
        ("async function deleteSelectedStudents()", "async function processBatchDelete()"),
        ("async function processBatchDelete()", "function deleteOneForBatch("),
        ("async function wipeAllFingerprints()", "async function wipeAllData()"),
        ("async function wipeAllData()", "function waitForWipe("),
    )
    for start, end in workflows:
        section = script[script.index(start):script.index(end)]
        assert "guardScanStopped(" in section


def test_role_switch_keeps_teacher_as_teacher():
    script = (WEB_ROOT / "app.js").read_text(encoding="utf-8")

    assert "function normalizeRoleKey" in script
    assert "return key in ROLE_LEVELS ? key : 'guest';" in script
    assert "const normalized = normalizeRoleKey(role);" in script


def test_v3_window_size_fits_common_small_windows():
    import importlib.util
    import sys
    import types
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    gui_web_dir = root / "python" / "gui_web"

    original_gui_pkg = sys.modules.get("gui_web")
    original_gui_api = sys.modules.get("gui_web.api")
    original_webview = sys.modules.get("webview")
    original_core_logger = sys.modules.get("core.logger")
    original_api = sys.modules.get("api")

    try:
        fake_webview = types.ModuleType("webview")
        fake_webview.create_window = lambda *args, **kwargs: kwargs
        fake_webview.start = lambda *args, **kwargs: None
        sys.modules["webview"] = fake_webview

        fake_log = types.SimpleNamespace(
            info=lambda *args, **kwargs: None,
            warning=lambda *args, **kwargs: None,
            error=lambda *args, **kwargs: None,
            exception=lambda *args, **kwargs: None,
            success=lambda *args, **kwargs: None,
        )
        sys.modules["core.logger"] = types.ModuleType("core.logger")
        sys.modules["core.logger"].log = fake_log

        fake_api = types.ModuleType("api")
        fake_api.Api = object
        sys.modules["api"] = fake_api

        fake_pkg_api = types.ModuleType("gui_web.api")
        fake_pkg_api.Api = object

        gui_pkg = types.ModuleType("gui_web")
        gui_pkg.__path__ = [str(gui_web_dir)]
        gui_pkg.api = fake_pkg_api
        sys.modules["gui_web"] = gui_pkg
        sys.modules["gui_web.api"] = fake_pkg_api

        spec = importlib.util.spec_from_file_location("gui_web.main_web", gui_web_dir / "main_web.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules["gui_web.main_web"] = module
        spec.loader.exec_module(module)

        width, height = module.resolve_window_size(1024, 768)
        assert width <= 1024 - 40
        assert height <= 768 - 40
        assert width >= 760
        assert height >= 540
    finally:
        if original_gui_pkg is None:
            sys.modules.pop("gui_web", None)
        else:
            sys.modules["gui_web"] = original_gui_pkg
        if original_gui_api is None:
            sys.modules.pop("gui_web.api", None)
        else:
            sys.modules["gui_web.api"] = original_gui_api
        if original_webview is None:
            sys.modules.pop("webview", None)
        else:
            sys.modules["webview"] = original_webview
        if original_core_logger is None:
            sys.modules.pop("core.logger", None)
        else:
            sys.modules["core.logger"] = original_core_logger
        if original_api is None:
            sys.modules.pop("api", None)
        else:
            sys.modules["api"] = original_api


def test_enrollment_requires_connection_and_blocks_while_scanning():
    script = (WEB_ROOT / "app.js").read_text(encoding="utf-8")

    assert "ESP32 not connected. Connect first before enrolling a student." in script
    assert "Stop attendance scanning before enrolling a student." in script
    assert "if (!connected) {" in script
    assert "if (scanning) {" in script


def test_v3_validation_api_returns_field_feedback(monkeypatch):
    from gui_web.api import Api

    class Result:
        def __init__(self, valid, state, message):
            self.valid = valid
            self.state = type("State", (), {"value": state})()
            self.message = message

    monkeypatch.setattr("gui_web.api.db.get_student_field_feedback", lambda *args: {
        "student_no": Result(False, "missing", "Required field"),
        "student_name": Result(True, "valid", "Valid"),
    })

    result = Api().validate_student_fields("", "Alice", "", "")

    assert result["all_valid"] is False
    assert result["fields"]["student_no"]["message"] == "Required field"


def test_v3_statistics_report_includes_students_without_attendance(monkeypatch):
    from gui_web.api import Api

    api = Api()
    monkeypatch.setattr("gui_web.api.permissions.has_permission", lambda action: True)
    monkeypatch.setattr("gui_web.api.db.get_all_students", lambda: [
        {"fingerprint_id": 1, "student_name": "Alice", "student_no": "S-001", "grade": "10", "section": "A"},
        {"fingerprint_id": 2, "student_name": "Bob", "student_no": "S-002", "grade": "10", "section": "A"},
    ])
    monkeypatch.setattr("gui_web.api.db.get_attendance_all", lambda: [{
        "student_name": "Alice", "student_no": "S-001", "grade": "10",
        "section": "A", "date": "2026-09-10", "status": "Present",
    }])
    monkeypatch.setattr(api.serial, "is_connected", lambda: False)

    result = api.get_statistics_report()

    assert result["total_students"] == 2
    assert result["avg_per_student"] == 0.5
    assert [student["student_name"] for student in result["all_students"]] == ["Alice", "Bob"]
    assert result["all_students"][1]["count"] == 0
    assert result["by_grade"] == {"10": 2}
    assert result["recent_attendance"] == [{"date": "2026-09-10", "count": 1}]
    assert result["enrolled_by_grade"] == {"10": 2}
    assert result["attendance_by_grade"] == [{"grade": "10", "count": 1}]
    assert result["students_by_section"] == [{"section": "A", "count": 2}]
    assert result["attendance_timeline"] == [{"date": "2026-09-10", "count": 1}]
    assert result["connected"] is False


def test_v3_serial_troubleshooting_message_uses_detected_ports(monkeypatch):
    from gui_web.api import Api

    api = Api()
    monkeypatch.setattr(api, "list_ports", lambda: ["COM7"])

    result = api.get_serial_troubleshooting()

    assert result["ports"] == ["COM7"]
    assert "Detected ports: COM7" in result["message"]
    assert "Device Manager" in result["message"]
    assert "CP210x" in result["message"]


def test_v3_profiler_collects_and_reports_enabled_measurements(capsys):
    from gui_web.perf_profiler import PerfProfiler

    profiler = PerfProfiler(enabled=True)
    profiler.start("students.load")
    profiler.stop("students.load")
    profiler.stop("missing")
    profiler.report()

    output = capsys.readouterr().out
    assert "Performance report (entries=1)" in output
    assert "students.load" in output
    assert "count=1" in output


def test_v3_profiler_is_inert_when_disabled(capsys):
    from gui_web.perf_profiler import PerfProfiler

    profiler = PerfProfiler(enabled=False)
    profiler.start("students.load")
    profiler.stop("students.load")
    profiler.report()

    assert capsys.readouterr().out == ""


def test_v3_web_bundle_uses_native_unicode_display_values():
    script = (WEB_ROOT / "app.js").read_text(encoding="utf-8")
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")

    assert "repairWebviewMojibake" not in script
    assert "return String(value == null ? '' : value)" in script
    assert "textContent = student.student_name" in script
    assert "${escapeHtml(r.student_name)}" in script
    assert 'id="student-status-today"' in html
    assert 'id="set-time-in"' in html
    assert html.count('id="det-status"') == 0
    assert "getElementById('student-status-today')" in script


def test_v3_student_detail_returns_today_attendance_status(monkeypatch):
    from gui_web.api import Api

    api = Api()
    permissions.set_session_role("teacher", 600.0)
    monkeypatch.setattr("gui_web.api.db.get_student", lambda fingerprint_id: {
        "fingerprint_id": fingerprint_id,
        "student_name": "Alice",
    })
    monkeypatch.setattr("gui_web.api.datetime", __import__("datetime").datetime)
    monkeypatch.setattr("gui_web.api.db.get_attendance_by_date", lambda date: [{
        "fingerprint_id": 7,
        "event_type": "time_in",
        "time": "08:20:00",
    }])
    monkeypatch.setattr("gui_web.api.load_settings", lambda: {
        "time_in": "08:00", "time_out": "17:00",
        "early_threshold_minutes": 15, "late_threshold_minutes": 15,
        "absent_threshold_minutes": 60,
    })

    student = api.get_student(7)

    assert student["attendance_status"] == "Late"


def test_v3_student_detail_without_scan_is_absent(monkeypatch):
    from gui_web.api import Api

    api = Api()
    permissions.set_session_role("teacher", 600.0)
    monkeypatch.setattr("gui_web.api.db.get_student", lambda fingerprint_id: {
        "fingerprint_id": fingerprint_id,
        "student_name": "Alice",
    })
    monkeypatch.setattr("gui_web.api.db.get_attendance_by_date", lambda date: [])

    assert api.get_student(7)["attendance_status"] == "Absent"


def test_v3_push_json_round_trips_unicode_names():
    from gui_web.api import Api

    api = Api()
    api.set_window(MagicMock())
    payload = {"student": {"student_name": "José, María Ñ"}}
    api._push("scan_result", payload)

    script = api._window.evaluate_js.call_args.args[0]
    expected_json = json.dumps(payload, default=str, ensure_ascii=True, allow_nan=False)
    assert expected_json in script
    assert "José" not in script
    assert json.loads(expected_json)["student"]["student_name"] == payload["student"]["student_name"]


def test_v3_student_csv_round_trips_unicode(tmp_path):
    from gui_web.api import Api

    path = tmp_path / "students.csv"
    result = Api()._rows_to_csv(
        [{"student_name": "Garcia, José R.", "student_no": "S-004"}], path
    )

    assert result["ok"] is True
    assert path.read_text(encoding="utf-8-sig").splitlines()[0] == "student_name,Student LRN"
    assert "Garcia, José R." in path.read_text(encoding="utf-8-sig")


def test_v3_csv_preserves_long_student_numbers_and_attendance_status(tmp_path):
    from gui_web.api import Api

    path = tmp_path / "attendance.csv"
    result = Api()._rows_to_csv(
        [{
            "student_no": "123456789012",
            "student_name": "María Ñ",
            "time_in": "08:00:00",
            "time_out": "",
            "attendance_status": "Present",
        }],
        path,
    )

    assert result["ok"] is True
    content = path.read_text(encoding="utf-8-sig")
    assert "'123456789012" in content
    assert "María Ñ" in content
    assert "Present" in content
    assert ",,Present" in content


def test_v3_today_export_uses_visible_fallback_rows(monkeypatch):
    from gui_web.api import Api

    api = Api()
    api._rows_to_csv = MagicMock(return_value={"ok": True})
    api._choose_csv_path = MagicMock(return_value=Path("C:/chosen/attendance.csv"))
    visible_rows = [{
        "student_no": "S-004",
        "student_name": "Garcia, José R.",
        "grade": "12",
        "section": "A",
        "date": "2026-09-10",
        "time": "08:00:00",
        "confidence": 200,
        "status": "GOOD MATCH",
        "event_type": "time_in",
    }]
    monkeypatch.setattr("gui_web.api.permissions.require_permission", lambda action: True)
    monkeypatch.setattr("gui_web.api.db.export_attendance_range_with_time_in_out", lambda start, end: [])
    monkeypatch.setattr("gui_web.api.db.get_attendance_today", lambda: visible_rows)
    monkeypatch.setattr(
        "gui_web.api.db.export_attendance_rows_with_time_in_out",
        lambda rows: [{"student_name": rows[0]["student_name"], "time_in": rows[0]["time"]}],
    )

    result = api.export_attendance_csv("today")

    assert result == {"ok": True}
    exported_rows = api._rows_to_csv.call_args.args[0]
    assert exported_rows == [{"student_name": "Garcia, José R.", "time_in": "08:00:00", "attendance_status": "Present"}]
    assert api._rows_to_csv.call_args.args[1] == Path("C:/chosen/attendance.csv")


def test_v3_csv_export_cancel_does_not_write_to_default_folder(monkeypatch):
    from gui_web.api import Api

    api = Api()
    api._choose_csv_path = MagicMock(return_value=None)
    api._rows_to_csv = MagicMock()
    monkeypatch.setattr("gui_web.api.permissions.require_permission", lambda action: True)
    monkeypatch.setattr("gui_web.api.db.export_attendance_range_with_time_in_out", lambda start, end: [{"student_name": "A"}])

    result = api.export_attendance_csv("today")

    assert result == {"ok": False, "message": "Export cancelled."}
    api._rows_to_csv.assert_not_called()


def test_v3_csv_save_dialog_uses_pywebview_save_contract():
    from gui_web.api import Api, CONFIG
    import webview

    window = MagicMock()
    window.create_file_dialog.return_value = ("C:/chosen/attendance.csv",)
    api = Api()
    api.set_window(window)

    selected = api._choose_csv_path("attendance_today.csv")

    assert selected == Path("C:/chosen/attendance.csv")
    window.create_file_dialog.assert_called_once_with(
        dialog_type=webview.FileDialog.SAVE,
        directory=str(CONFIG.export_folder),
        save_filename="attendance_today.csv",
        file_types=("CSV files (*.csv)", "All files (*.*)"),
    )


def test_v3_all_students_export_includes_attendance_columns(monkeypatch):
    from gui_web.api import Api

    api = Api()
    permissions.set_session_role("teacher", 600.0)
    api._choose_csv_path = MagicMock(return_value=Path("C:/chosen/students.csv"))
    api._rows_to_csv = MagicMock(return_value={"ok": True})
    monkeypatch.setattr("gui_web.api.permissions.require_permission", lambda action: True)
    monkeypatch.setattr("gui_web.api.datetime", MagicMock(now=lambda: __import__("datetime").datetime(2026, 9, 11)))
    monkeypatch.setattr("gui_web.api.load_settings", lambda: {
        "time_in": "08:00", "time_out": "17:00",
        "early_threshold_minutes": 15, "late_threshold_minutes": 15,
        "absent_threshold_minutes": 60,
    })
    monkeypatch.setattr("gui_web.api.db.get_all_students", lambda: [
        {"student_no": "123456789012", "student_name": "Álvaro", "grade": "12", "section": "A"},
        {"student_no": "2", "student_name": "Zoe", "grade": "12", "section": "A"},
    ])
    monkeypatch.setattr("gui_web.api.db.export_attendance_range_with_time_in_out", lambda start, end: [{
        "student_no": "123456789012", "time_in": "08:00:00", "time_out": "",
        "match_status": "GOOD MATCH",
    }])

    result = api.export_students_csv()

    assert result == {"ok": True}
    rows = api._rows_to_csv.call_args.args[0]
    assert [row["student_name"] for row in rows] == ["Álvaro", "Zoe"]
    assert rows[0]["time_in"] == "08:00:00"
    assert rows[0]["time_out"] == ""
    assert rows[0]["attendance_status"] == "Present"
    assert rows[1]["attendance_status"] == "Absent"


def test_v3_all_students_export_uses_attendance_date(monkeypatch):
    from gui_web.api import Api

    api = Api()
    permissions.set_session_role("teacher", 600.0)
    api._choose_csv_path = MagicMock(return_value=Path("C:/chosen/students.csv"))
    api._rows_to_csv = MagicMock(return_value={"ok": True})
    monkeypatch.setattr("gui_web.api.permissions.require_permission", lambda action: True)
    monkeypatch.setattr("gui_web.api.datetime", MagicMock(now=lambda: __import__("datetime").datetime(2026, 9, 20)))
    monkeypatch.setattr("gui_web.api.load_settings", lambda: {
        "time_in": "08:00", "time_out": "17:00",
        "early_threshold_minutes": 15, "late_threshold_minutes": 15,
        "absent_threshold_minutes": 60,
        "school_calendar": {
            "2026-09-19": {
                "type": "half_day",
                "time_in": "13:00",
                "time_out": "17:00",
            }
        },
    })
    monkeypatch.setattr("gui_web.api.db.get_all_students", lambda: [
        {
            "student_no": "1",
            "student_name": "Alice",
            "grade": "12",
            "section": "A",
        },
    ])
    monkeypatch.setattr(
        "gui_web.api.db.export_attendance_range_with_time_in_out",
        lambda start, end: [{
            "student_no": "1",
            "date": "2026-09-19",
            "time_in": "12:00:00",
            "time_out": "",
            "match_status": "GOOD MATCH",
        }],
    )

    result = api.export_students_csv()

    assert result == {"ok": True}
    exported = api._rows_to_csv.call_args.args[0][0]
    assert exported["attendance_status"] == "Early"


def test_v3_attendance_page_uses_date_specific_schedule(monkeypatch):
    from gui_web.api import Api

    api = Api()
    permissions.set_session_role("teacher", 600.0)
    monkeypatch.setattr("gui_web.api.permissions.require_permission", lambda action: True)
    monkeypatch.setattr("gui_web.api.db.export_attendance_range", lambda start, end: [{
        "fingerprint_id": 1,
        "date": "2026-09-20",
        "time": "12:00:00",
        "event_type": "time_out",
        "status": "GOOD MATCH",
    }])
    monkeypatch.setattr("gui_web.api.load_settings", lambda: {
        "time_in": "08:00", "time_out": "17:00",
        "early_threshold_minutes": 15, "late_threshold_minutes": 15,
        "absent_threshold_minutes": 60,
        "school_calendar": {
            "2026-09-20": {
                "type": "half_day",
                "time_in": "08:00",
                "time_out": "12:00",
            }
        },
    })

    result = api.get_attendance(mode="last30")

    assert result["rows"][0]["attendance_status"] == "Out"


def test_v3_global_schedule_rejects_time_out_before_time_in(monkeypatch):
    from gui_web.api import Api

    api = Api()
    monkeypatch.setattr("gui_web.api.permissions.require_role", lambda required_role: True)
    monkeypatch.setattr("gui_web.api.load_settings", lambda: {
        "time_in": "08:00",
        "time_out": "17:00",
        "cooldown": 10,
        "min_confidence": 96,
        "auto_backup_interval_minutes": 25,
        "early_threshold_minutes": 15,
        "late_threshold_minutes": 15,
        "absent_threshold_minutes": 0,
    })
    monkeypatch.setattr("gui_web.api.save_settings", lambda settings: None)
    result = api.save_ui_settings({
        "time_in": "17:00",
        "time_out": "08:00",
    })

    assert result["ok"] is False
    assert "Time Out must be later than Time In." == result["message"]


def test_v3_calendar_bulk_half_day_uses_valid_times(monkeypatch):
    from gui_web.api import Api

    api = Api()
    captured = {}

    def fake_load_settings():
        return {
            "time_in": "08:00",
            "time_out": "17:00",
            "school_calendar": {},
        }

    def fake_save_settings(settings):
        captured["settings"] = settings
        return None

    monkeypatch.setattr("gui_web.api.permissions.has_permission", lambda action: True)
    monkeypatch.setattr("gui_web.api.load_settings", fake_load_settings)
    monkeypatch.setattr("gui_web.api.save_settings", fake_save_settings)

    result = api.set_calendar_entry("2026-09-22", "half_day", "Exam", "08:30", "12:30")

    assert result["ok"] is True
    assert result["entry"]["time_in"] == "08:30"
    assert result["entry"]["time_out"] == "12:30"
    assert captured["settings"]["school_calendar"]["2026-09-22"]["type"] == "half_day"


def test_v3_attendance_evaluation_ignores_weekend_activity(monkeypatch):
    from gui_web.api import Api

    api = Api()
    monkeypatch.setattr("gui_web.api.permissions.has_permission", lambda action: True)
    monkeypatch.setattr("gui_web.api.load_settings", lambda: {
        "school_calendar": {},
    })
    monkeypatch.setattr("gui_web.api.db.get_daily_attendance_summary", lambda start_date, end_date: [
        {"student_no": "1", "date": "2026-09-19"},
        {"student_no": "1", "date": "2026-09-20"},
    ])
    monkeypatch.setattr("gui_web.api.db.get_all_students", lambda: [{
        "fingerprint_id": 1,
        "student_no": "1",
        "student_name": "Alice",
        "grade": "12",
        "section": "A",
        "enrollment_date": "2026-09-01T00:00:00",
    }])

    result = api.get_attendance_evaluation("week", "2026-09-20")

    assert result["school_days"] == []
    assert result["total_days"] == 0
    assert result["rows"][0]["attendance_rate"] is None


def test_v3_recent_export_uses_visible_page(monkeypatch):
    from gui_web.api import Api

    api = Api()
    api._choose_csv_path = MagicMock(return_value=Path("C:/chosen/recent.csv"))
    api._rows_to_csv = MagicMock(return_value={"ok": True})
    recent_rows = [{
        "student_no": "S-1", "student_name": "Alice", "grade": "12", "section": "A",
        "date": "2026-09-11", "time": "08:00:00", "confidence": 200,
        "status": "GOOD MATCH", "event_type": "time_in", "fingerprint_id": 1,
    }]
    monkeypatch.setattr("gui_web.api.permissions.require_permission", lambda action: True)
    monkeypatch.setattr("gui_web.api.db.get_attendance_paginated", lambda limit, offset: recent_rows)
    monkeypatch.setattr("gui_web.api.db.export_attendance_rows_with_time_in_out", lambda rows: [{
        "student_name": rows[0]["student_name"], "time_in": rows[0]["time"], "time_out": "",
    }])
    monkeypatch.setattr("gui_web.api.db.export_attendance_range_with_time_in_out", lambda start, end: pytest.fail("Recent must not query a date range"))

    result = api.export_attendance_csv("recent", 100)

    assert result == {"ok": True}
    assert api._rows_to_csv.call_args.args[0][0]["student_name"] == "Alice"


def test_v3_weekly_export_uses_seven_day_date_range(monkeypatch):
    from gui_web.api import Api

    api = Api()
    api._choose_csv_path = MagicMock(return_value=Path("C:/chosen/weekly.csv"))
    api._rows_to_csv = MagicMock(return_value={"ok": True})
    captured = {}
    monkeypatch.setattr("gui_web.api.permissions.require_permission", lambda action: True)
    def export_range(start, end):
        captured["range"] = (start, end)
        return [{"student_name": "Alice", "time_in": "08:00:00", "time_out": ""}]
    monkeypatch.setattr("gui_web.api.db.export_attendance_range_with_time_in_out", export_range)

    result = api.export_attendance_csv("weekly")

    assert result == {"ok": True}
    start, end = captured["range"]
    assert (datetime.strptime(end, "%Y-%m-%d") - datetime.strptime(start, "%Y-%m-%d")).days == 6


def test_v3_weekly_export_uses_selected_calendar_week(monkeypatch):
    from gui_web.api import Api

    api = Api()
    api._choose_csv_path = MagicMock(return_value=Path("C:/chosen/weekly.csv"))
    api._rows_to_csv = MagicMock(return_value={"ok": True})
    captured = {}
    monkeypatch.setattr("gui_web.api.permissions.require_permission", lambda action: True)
    def export_range(start, end):
        captured["range"] = (start, end)
        return [{"time_in": "08:00:00"}]
    monkeypatch.setattr("gui_web.api.db.export_attendance_range_with_time_in_out", export_range)

    result = api.export_attendance_csv("weekly", week_start="2026-09-07")

    assert result == {"ok": True}
    assert captured["range"] == ("2026-09-07", "2026-09-13")


def test_restore_publishes_v3_data_refresh_event(monkeypatch):
    from gui_web.api import Api

    api = Api()
    api._push = MagicMock()
    monkeypatch.setattr("gui_web.api.permissions.require_permission", lambda action: True)
    monkeypatch.setattr("gui_web.api.db.restore_database", lambda path: (True, "Restored"))

    result = api.restore_backup("backup.zip")

    assert result == {"ok": True, "message": "Restored"}
    api._push.assert_called_once_with("data_changed", {"reason": "restore"})


def test_v3_styles_define_narrow_window_layout_rules():
    styles = (WEB_ROOT / "styles.css").read_text(encoding="utf-8")
    assert "@media" in styles
    assert "max-width" in styles
    assert "overflow" in styles
