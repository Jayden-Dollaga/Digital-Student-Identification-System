import sys
import unittest
from pathlib import Path
from unittest import mock

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QObject, Signal

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from core import database
from core import permissions
from gui_qt.pages.reports_page import ReportsPage
from gui_qt.pages.students_page import StudentsPage, ConfirmDeleteDialog


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
        """delete_student() raising PermissionError must be handled cleanly
        by ConfirmDeleteDialog: no uncaught exception, a clean user-facing
        message, and the student must NOT be deleted.

        NOTE: on_delete_clicked() now shows ConfirmDeleteDialog and calls
        .exec() on it - a real blocking modal with no one to click it in an
        automated test. So this drives the dialog directly instead of going
        through on_delete_clicked(), which would hang the test suite.
        """
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

        fake_worker = _FakeDeleteWorker()

        def delete_from_db(fingerprint_id):
            with mock.patch.object(permissions, "get_current_role", return_value="guest"):
                return database.delete_student(fingerprint_id)

        dialog = ConfirmDeleteDialog(
            fingerprint_ids=[7],
            device_connected=True,
            serial_handler=mock.MagicMock(),
            serial_worker=fake_worker,
            delete_from_db=delete_from_db,
        )

        with mock.patch(
            "gui_qt.pages.students_page.cmd_delete", return_value=True
        ), mock.patch(
            "gui_qt.pages.students_page.QMessageBox.warning"
        ) as mock_warning:
            dialog.on_confirm()  # must not raise
            fake_worker.delete_progress.emit({"event": "success", "id": 7})

        mock_warning.assert_called_once()
        self.assertIsNotNone(database.get_student(7))

    def test_delete_succeeds_for_authorized_role(self):
        """Control case: the same flow must actually delete when the role
        does have permission, so the fix above isn't just blocking everything."""
        ok, msg = self.page.save_student_details(
            8,
            {
                "student_no": "S-008",
                "student_name": "Carol Example",
                "grade": "10",
                "section": "A",
            },
        )
        self.assertTrue(ok, msg)

        fake_worker = _FakeDeleteWorker()

        def delete_from_db(fingerprint_id):
            with mock.patch.object(permissions, "get_current_role", return_value="admin"):
                return database.delete_student(fingerprint_id)

        dialog = ConfirmDeleteDialog(
            fingerprint_ids=[8],
            device_connected=True,
            serial_handler=mock.MagicMock(),
            serial_worker=fake_worker,
            delete_from_db=delete_from_db,
        )

        with mock.patch("gui_qt.pages.students_page.cmd_delete", return_value=True):
            dialog.on_confirm()
            fake_worker.delete_progress.emit({"event": "success", "id": 8})

        self.assertIsNone(database.get_student(8))

    def test_delete_disabled_while_disconnected(self):
        """Deleting while disconnected must not touch the database at all -
        not even attempt it and fail, just never call delete_from_db."""
        ok, msg = self.page.save_student_details(
            9,
            {
                "student_no": "S-009",
                "student_name": "Dan Example",
                "grade": "10",
                "section": "A",
            },
        )
        self.assertTrue(ok, msg)

        delete_from_db = mock.MagicMock()
        dialog = ConfirmDeleteDialog(
            fingerprint_ids=[9],
            device_connected=False,
            serial_handler=None,
            serial_worker=None,
            delete_from_db=delete_from_db,
        )

        dialog.on_confirm()  # must not raise, must not delete

        delete_from_db.assert_not_called()
        self.assertIsNotNone(database.get_student(9))


class _FakeDeleteWorker(QObject):
    """Minimal stand-in for SerialWorker exposing just the signal
    ConfirmDeleteDialog connects to, so tests can drive delete progress
    without spinning up the real threaded worker or any hardware."""
    delete_progress = Signal(dict)


if __name__ == "__main__":
    unittest.main()
