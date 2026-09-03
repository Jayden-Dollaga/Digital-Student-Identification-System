import sys
import unittest
from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Python"))

from task_manager_window import TaskManagerWindow


class TaskManagerVariantTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_task_manager_shell_has_icon_navigation(self):
        window = TaskManagerWindow()
        self.assertEqual(window.stack.count(), 7)
        self.assertEqual(len(window._nav_buttons), 7)
        self.assertTrue(all(not button.icon().isNull() for button in window._nav_buttons))
        self.assertTrue(all(button.iconSize() == QSize(18, 18) for button in window._nav_buttons))
        window.close()

    def test_compact_mode_keeps_icons_and_hides_labels(self):
        window = TaskManagerWindow()
        window.density_button.setChecked(True)
        self.assertEqual(window.sidebar.width(), 64)
        self.assertTrue(all(button.text() == "" for button in window._nav_buttons))
        self.assertTrue(all(not button.icon().isNull() for button in window._nav_buttons))
        window.close()

    def test_identification_page_is_still_the_primary_workflow(self):
        window = TaskManagerWindow()
        window._select_page("Identify")
        self.assertEqual(window.page_title.text(), "Identify")
        window.results.setCurrentRow(3)
        self.assertEqual(window.match_state.text(), "REVIEW REQUIRED")
        window.close()


if __name__ == "__main__":
    unittest.main()
