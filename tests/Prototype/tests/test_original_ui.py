import sys
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Python"))

from original_window import OriginalUIWindow


class OriginalUITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_original_shell_has_six_sections(self):
        window = OriginalUIWindow()
        self.assertEqual(window.stack.count(), 6)
        self.assertEqual([button.property("navName") for button in window._nav_buttons], list(OriginalUIWindow.NAVIGATION))
        self.assertEqual(window.page_title.text(), "Dashboard")
        window.close()

    def test_original_shell_has_connection_and_scan_controls(self):
        window = OriginalUIWindow()
        self.assertEqual(window.connect_button.text(), "Connect")
        window.connect_button.click()
        self.assertEqual(window.connect_button.text(), "Disconnect")
        window.scan_toggle_button.click()
        self.assertEqual(window.page_title.text(), "Attendance")
        window.close()

    def test_original_compact_sidebar_preserves_navigation(self):
        window = OriginalUIWindow()
        window.density_button.setChecked(True)
        self.assertEqual(window.sidebar.width(), 68)
        self.assertTrue(all(button.text() == "" for button in window._nav_buttons))
        window._select_page("Reports")
        self.assertTrue(window._nav_buttons[3].isChecked())
        window.close()


if __name__ == "__main__":
    unittest.main()
