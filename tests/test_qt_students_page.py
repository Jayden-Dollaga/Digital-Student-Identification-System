import sys
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from core import database
from gui_qt.pages.students_page import StudentsPage


class QtStudentsPageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        database.init_database()
        database.clear_all_data()
        self.page = StudentsPage()

    def test_save_student_details_persists_student_and_refreshes_table(self):
        ok, msg = self.page.save_student_details(
            42,
            {
                "student_no": "S-042",
                "student_name": "Alice Example",
                "grade": "11",
                "section": "A",
            },
        )

        self.assertTrue(ok, msg)
        saved = database.get_student(42)
        self.assertIsNotNone(saved)
        self.assertEqual(saved["student_name"], "Alice Example")
        self.assertEqual(self.page.table.rowCount(), 1)
        self.assertEqual(self.page.table.item(0, 1).text(), "S-042")


if __name__ == "__main__":
    unittest.main()
