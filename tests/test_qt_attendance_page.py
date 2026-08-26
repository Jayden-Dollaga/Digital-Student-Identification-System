import sys
import unittest
from pathlib import Path
from unittest import mock

from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from core import database
from core import permissions
from gui_qt.pages.attendance_page import AttendancePage


class QtAttendancePageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        database.init_database()
        # clear_all_data() now enforces the "wipe" permission at the DB
        # layer - pin the role explicitly here so this test doesn't depend
        # on whatever role happens to be saved in a real settings.json.
        with mock.patch.object(permissions, "get_current_role", return_value="admin"):
            database.clear_all_data()
        self.page = AttendancePage()

    def test_empty_state_message_is_shown_when_no_records_exist(self):
        self.assertTrue(hasattr(self.page, "empty_label"))
        self.assertEqual(self.page.empty_label.text(), "No attendance records yet.")


if __name__ == "__main__":
    unittest.main()
