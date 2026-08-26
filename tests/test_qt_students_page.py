import sys
import unittest
from pathlib import Path
from unittest import mock

from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from core import database
from core import permissions
from gui_qt.pages.reports_page import ReportsPage
from gui_qt.pages.students_page import StudentsPage


class QtStudentsPageTest(unittest.TestCase):
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

    def test_unicode_name_persists_and_appears_in_qt_reports(self):
        ok, msg = self.page.save_student_details(
            99,
            {
                "student_no": "S-099",
                "student_name": "Łukasz Nowak",
                "grade": "12",
                "section": "ICT-12-1",
            },
        )

        self.assertTrue(ok, msg)

        saved = database.get_student(99)
        self.assertIsNotNone(saved)
        self.assertEqual(saved["student_name"], "Łukasz Nowak")
        self.assertEqual(self.page.table.item(0, 2).text(), "Łukasz Nowak")

        reports_page = ReportsPage()
        reports_page.refresh()
        report_text = reports_page.report_view.toPlainText()
        self.assertIn("Łukasz Nowak", report_text)

    def test_delete_blocked_shows_message_without_crashing_or_deleting(self):
        """on_delete_clicked() must handle the new PermissionError from
        delete_student() gracefully: no uncaught exception, a clean
        user-facing message, and the student must NOT be deleted."""
        from PySide6.QtWidgets import QMessageBox

        ok, msg = self.page.save_student_details(
            7,
            {
                "student_no": "S-007",
                "student_name": "Bob Example",
                "grade": "10",
                "section": "A",
            },
        )
        self.assertTrue(ok, msg)
        self.assertEqual(self.page.table.rowCount(), 1)
        self.page.table.selectRow(0)

        with mock.patch(
            "gui_qt.pages.students_page.QMessageBox.question", return_value=QMessageBox.Yes
        ), mock.patch(
            "gui_qt.pages.students_page.QMessageBox.warning"
        ) as mock_warning, mock.patch.object(
            permissions, "get_current_role", return_value="guest"
        ):
            self.page.on_delete_clicked()  # must not raise

        mock_warning.assert_called_once()
        self.assertIsNotNone(database.get_student(7))


if __name__ == "__main__":
    unittest.main()
