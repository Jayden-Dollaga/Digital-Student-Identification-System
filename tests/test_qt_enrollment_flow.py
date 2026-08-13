"""Test Qt enrollment dialog and student save flow end-to-end."""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add python to path
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from core.database import init_database, get_all_students, DB_PATH
from services.student_service import StudentService
from PySide6.QtWidgets import QApplication


class TestQtEnrollmentFlow(unittest.TestCase):
    """Verify enrollment dialog → save → database → table refresh flow."""

    @classmethod
    def setUpClass(cls):
        """Initialize Qt application once for all tests."""
        if not QApplication.instance():
            QApplication(sys.argv)

    def setUp(self):
        """Set up a fresh database for each test."""
        # Use a test database
        self.test_db = Path(__file__).parent / "test_enrollment.db"
        if self.test_db.exists():
            self.test_db.unlink()
        
        # Patch DB_PATH to use test database
        self.db_patch = patch("core.database.DB_PATH", str(self.test_db))
        self.db_patch.start()
        
        init_database()
        self.service = StudentService()

    def tearDown(self):
        """Clean up test database."""
        self.db_patch.stop()
        if self.test_db.exists():
            self.test_db.unlink()

    def test_save_student_and_retrieve(self):
        """Test saving a student and retrieving it."""
        # Simulate enrollment dialog completing with ID 5
        fingerprint_id = 5
        student_no = "S12345"
        student_name = "John Doe"
        grade = "10"
        section = "A"

        # Save the student
        ok, msg = self.service.save_student(
            fingerprint_id, student_no, student_name, grade, section
        )
        self.assertTrue(ok, f"Failed to save student: {msg}")

        # Retrieve all students (this is what refresh() does)
        all_students = self.service.get_all_students()
        self.assertEqual(len(all_students), 1, f"Expected 1 student, got {len(all_students)}")

        # Verify the student record
        student = all_students[0]
        self.assertEqual(student["fingerprint_id"], fingerprint_id)
        self.assertEqual(student["student_no"], student_no)
        self.assertEqual(student["student_name"], student_name)
        self.assertEqual(student["grade"], grade)
        self.assertEqual(student["section"], section)

    def test_multiple_enrollments(self):
        """Test enrolling multiple students."""
        students_to_enroll = [
            (1, "S001", "Alice", "9", "B"),
            (2, "S002", "Bob", "10", "A"),
            (3, "S003", "Charlie", "11", "C"),
        ]

        for fid, sno, name, grade, section in students_to_enroll:
            ok, msg = self.service.save_student(fid, sno, name, grade, section)
            self.assertTrue(ok, f"Failed to save {name}: {msg}")

        all_students = self.service.get_all_students()
        self.assertEqual(len(all_students), 3, f"Expected 3 students, got {len(all_students)}")

    def test_duplicate_fingerprint_id_updates_existing(self):
        """Test that saving with same fingerprint_id updates the existing record."""
        fingerprint_id = 5
        
        # First save succeeds
        ok, msg = self.service.save_student(
            fingerprint_id, "S001", "Student One", "10", "A"
        )
        self.assertTrue(ok, "First save should succeed")

        # Second save with same fingerprint_id should update the record
        ok, msg = self.service.save_student(
            fingerprint_id, "S002", "Student Two", "11", "B"
        )
        self.assertTrue(ok, "Second save with same ID should update, not fail")

        # Verify the record was updated
        student = self.service.get_student(fingerprint_id)
        self.assertIsNotNone(student)
        self.assertEqual(student["student_no"], "S002")
        self.assertEqual(student["student_name"], "Student Two")
        self.assertEqual(student["grade"], "11")
        self.assertEqual(student["section"], "B")

    def test_enrollment_to_table_refresh(self):
        """Simulate the full flow: save → get_all_students → table update."""
        # This simulates what happens in StudentsPage.on_enroll_clicked()
        # -> EnrollDialog.accept() -> save_student_details() -> refresh()

        # Step 1: Enrollment complete with ID 7
        fid = 7
        values = {
            "fingerprint_id": fid,
            "student_no": "S999",
            "student_name": "Test Student",
            "grade": "12",
            "section": "Z",
        }

        # Step 2: save_student_details equivalent
        ok, msg = self.service.save_student(
            values["fingerprint_id"],
            values["student_no"],
            values["student_name"],
            values["grade"],
            values["section"],
        )
        self.assertTrue(ok, f"Save failed: {msg}")

        # Step 3: refresh() equivalent - get_all_students
        all_students = self.service.get_all_students()
        self.assertEqual(len(all_students), 1, "After save, should have 1 student")
        
        # Step 4: Verify table would display correctly
        row = all_students[0]
        self.assertEqual(row["fingerprint_id"], fid)
        self.assertEqual(row["student_name"], "Test Student")


if __name__ == "__main__":
    unittest.main()
