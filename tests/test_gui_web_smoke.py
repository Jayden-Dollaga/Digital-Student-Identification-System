"""Static and bridge-level smoke checks for the V3 HTML/pywebview UI."""

from pathlib import Path
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
