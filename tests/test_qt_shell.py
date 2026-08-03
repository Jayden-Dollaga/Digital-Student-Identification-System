import sys
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication, QLabel

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from gui_qt.widgets.sidebar import Sidebar
from gui_qt.main_window import MainWindow
from gui_qt.pages.dashboard_page import DashboardPage
from gui_qt.pages.reports_page import ReportsPage


class QtShellTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_sidebar_contains_expected_navigation_items(self):
        sidebar = Sidebar()
        children = [btn.text() for btn in sidebar._group.buttons()]
        self.assertIn("Dashboard", children)
        self.assertIn("Students", children)
        self.assertIn("Settings", children)

    def test_main_window_constructs_with_pages(self):
        window = MainWindow()
        self.assertEqual(window.stack.count(), 6)
        window.close()

    def test_dashboard_page_displays_recent_activity_section(self):
        page = DashboardPage()
        labels = [widget.text() for widget in page.findChildren(QLabel) if isinstance(widget, QLabel) and widget.text()]
        self.assertTrue(any("Recent activity" in label for label in labels))
        page.close()

    def test_reports_page_displays_summary_label(self):
        page = ReportsPage()
        labels = [widget.text() for widget in page.findChildren(QLabel) if isinstance(widget, QLabel) and widget.text()]
        self.assertTrue(any("Report preview" in label for label in labels))
        page.close()


if __name__ == "__main__":
    unittest.main()
