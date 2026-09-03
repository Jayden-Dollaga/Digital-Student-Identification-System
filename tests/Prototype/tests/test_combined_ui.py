import sys
import unittest
from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QApplication, QWidget

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Python"))

from actual_ui_prototype import ActualUIPrototypeWindow
from combined_ui import CombinedUIWindow


class CombinedUITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_combines_real_pages_with_task_manager_navigation_icons(self):
        window = CombinedUIWindow()
        self.assertIsInstance(window, ActualUIPrototypeWindow)
        self.assertEqual(window.stack.count(), 6)
        buttons = window.sidebar._group.buttons()
        self.assertEqual(len(buttons), 6)
        self.assertTrue(all(not button.icon().isNull() for button in buttons))
        self.assertTrue(all(button.iconSize() == QSize(18, 18) for button in buttons))
        window.close()

    def test_real_page_navigation_and_preview_connection_are_preserved(self):
        window = CombinedUIWindow()
        window.sidebar._group.buttons()[2].click()
        self.assertEqual(window.page_title.text(), "Students")
        self.assertFalse(window.serial_handler.is_connected())
        self.assertIsInstance(window._pages["attendance"], QWidget)
        window.close()


if __name__ == "__main__":
    unittest.main()
