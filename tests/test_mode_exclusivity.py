import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from gui import app as gui_app


class ModeExclusivityTest(unittest.TestCase):
    def setUp(self):
        self.app = SimpleNamespace()
        self.app._closing = False
        self.app.serial_handler = SimpleNamespace(connected=True)
        self.app.enroll_dialog = None
        self.app.stop_button = SimpleNamespace(configure=lambda *args, **kwargs: None, cget=lambda key: "disabled")
        self.app.scan_button = SimpleNamespace(configure=lambda *args, **kwargs: None)
        self.app.enroll_button = SimpleNamespace(configure=lambda *args, **kwargs: None)
        self.app.wipe_button = SimpleNamespace(configure=lambda *args, **kwargs: None)
        self.app.log_message = lambda message: None
        self.app._ui_ready = lambda: True
        self.app.after = lambda *args, **kwargs: None
        self.app.tabview = SimpleNamespace(get=lambda: "📅 Attendance")
        self.app.attendance_mode = "Today"
        self.app.attendance_offset = 0
        self.app.has_permission = lambda permission: True
        self.app._set_command_mode_ui = gui_app.FingerprintApp._set_command_mode_ui.__get__(self.app, gui_app.FingerprintApp)
        self.app._set_wipe_mode_ui = gui_app.FingerprintApp._set_wipe_mode_ui.__get__(self.app, gui_app.FingerprintApp)
        self.app.start_scan = gui_app.FingerprintApp.start_scan.__get__(self.app, gui_app.FingerprintApp)
        self.app.enroll_sample = gui_app.FingerprintApp.enroll_sample.__get__(self.app, gui_app.FingerprintApp)
        self.app.open_wipe_dialog = gui_app.FingerprintApp.open_wipe_dialog.__get__(self.app, gui_app.FingerprintApp)
        self.app.close_wipe_dialog = gui_app.FingerprintApp.close_wipe_dialog.__get__(self.app, gui_app.FingerprintApp)

    def test_cannot_start_scan_during_wipe(self):
        self.app.wipe_mode_active = True
        self.app.enroll_mode_active = False
        self.app.scan_mode_active = False
        self.app.serial_handler.connected = True

        with patch.object(gui_app, "cmd_scan", return_value=True) as mock_scan:
            self.app.start_scan()
            mock_scan.assert_not_called()

    def test_cannot_enroll_during_wipe(self):
        self.app.wipe_mode_active = True
        self.app.enroll_mode_active = False
        self.app.scan_mode_active = False
        self.app.serial_handler.connected = True

        with patch.object(gui_app, "cmd_enroll", return_value=True) as mock_enroll:
            self.app.enroll_sample()
            mock_enroll.assert_not_called()

    def test_wipe_dialog_sets_and_clears_wipe_mode(self):
        self.app.wipe_mode_active = False
        self.app.has_permission = lambda permission: True
        self.app.wipe_button = SimpleNamespace(configure=lambda *args, **kwargs: None)
        self.app._set_wipe_mode_ui = gui_app.FingerprintApp._set_wipe_mode_ui.__get__(self.app, gui_app.FingerprintApp)
        self.app.close_wipe_dialog = gui_app.FingerprintApp.close_wipe_dialog.__get__(self.app, gui_app.FingerprintApp)

        self.app._set_wipe_mode_ui()
        self.assertTrue(self.app.wipe_mode_active)

        with patch.object(gui_app, "close_wipe_dialog", return_value=True):
            self.app.close_wipe_dialog()
        self.assertFalse(self.app.wipe_mode_active)


if __name__ == "__main__":
    unittest.main()
