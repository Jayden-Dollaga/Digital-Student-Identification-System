"""Static and bridge-level smoke checks for the V3 HTML/pywebview UI."""

from pathlib import Path
import json
import sys
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "python" / "gui_web" / "web"
PYTHON_ROOT = ROOT / "python"
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))


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
        "wipeAllFingerprints",
        "restoreBackup",
    ):
        assert f"function {workflow}" in script
    for event in ("connection_status", "mode_changed", "enroll_progress", "delete_progress", "wipe_progress", "data_changed"):
        assert event in script
    assert "<th>Attendance</th>" in html
    assert "&#9664; Prev" in html
    assert "Next &#9654;" in html
    assert "attendance_status" in script
    assert "attendanceBadgeClass" in script


def test_v3_web_bundle_uses_native_unicode_display_values():
    script = (WEB_ROOT / "app.js").read_text(encoding="utf-8")

    assert "repairWebviewMojibake" not in script
    assert "return String(value == null ? '' : value)" in script
    assert "textContent = student.student_name" in script
    assert "${escapeHtml(r.student_name)}" in script


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
