import sys
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from gui_qt.main_window import MainWindow


class QtMainWindowScanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_scan_is_blocked_when_enrollment_dialog_is_active(self):
        window = MainWindow.__new__(MainWindow)
        window._scan_blocked = True

        self.assertFalse(window._can_start_scan())
        self.assertIn("enrollment", window._scan_command_blocked_reason().lower())


if __name__ == "__main__":
    unittest.main()
