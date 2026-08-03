import sys
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from core.serial_handler import SerialHandler
from gui_qt.pages.logs_page import LogsPage
from gui_qt.pages.settings_page import SettingsPage


class QtSettingsLogsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_logs_page_clear_restores_ready_message(self):
        page = LogsPage()
        page.append_line("hello")
        page.clear()
        self.assertIn("System ready.", page.console.toPlainText())

    def test_settings_page_initializes_with_serial_handler(self):
        page = SettingsPage(serial_handler=SerialHandler())
        self.assertIsNotNone(page.port_combo)
        self.assertIsNotNone(page.baud_combo)


if __name__ == "__main__":
    unittest.main()
