import sys
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Python"))

from actual_ui_prototype import ActualUIPrototypeWindow


class ActualUIPrototypeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_uses_real_application_pages(self):
        window = ActualUIPrototypeWindow()
        self.assertEqual(window.stack.count(), 6)
        self.assertEqual(window.sidebar._group.buttons()[0].text(), "Dashboard")
        self.assertEqual(window._pages["students"].__class__.__name__, "StudentsPage")
        self.assertEqual(window._pages["logs"].__class__.__name__, "LogsPage")
        window.close()

    def test_navigation_is_display_only(self):
        window = ActualUIPrototypeWindow()
        window.sidebar._group.buttons()[1].click()
        self.assertEqual(window.page_title.text(), "Attendance")
        self.assertFalse(window.serial_handler.is_connected())
        window.close()


if __name__ == "__main__":
    unittest.main()
