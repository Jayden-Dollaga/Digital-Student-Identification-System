import sys
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication, QTableWidget

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Python"))

from hybrid_window import HybridWindow


class HybridPrototypeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_hybrid_shell_has_full_app_navigation(self):
        window = HybridWindow()
        self.assertEqual(window.stack.count(), 7)
        self.assertEqual([button.text() for button in window._nav_buttons], list(HybridWindow.NAVIGATION))
        window.close()

    def test_hybrid_pages_have_utility_content(self):
        window = HybridWindow()
        window._select_page("Attendance")
        self.assertEqual(len(window.findChildren(QTableWidget)), 2)
        window._select_page("Identify")
        window.results.setCurrentRow(3)
        self.assertEqual(window.match_state.text(), "REVIEW REQUIRED")
        window.close()


if __name__ == "__main__":
    unittest.main()
