"""Regression tests for Fix #4: user-facing errors must not expose raw
exception details (filesystem paths, database paths, internal
implementation details). The detailed exception should still reach the
application's logging system - only the text shown to the user changes.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

import core.database as database


class TestReportGenerationErrorSanitization:
    def test_generate_statistics_report_hides_raw_exception_on_failure(self):
        """Force an internal failure and confirm the returned report text
        is a safe, generic message - not the raw exception or a path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "attendance.db"
            with patch.object(database, "DB_PATH", str(db_path)):
                database.init_database()

                # Force a failure partway through report generation by
                # making the underlying connection blow up with a message
                # that would be very revealing if ever shown to a user.
                sensitive_detail = f"unable to open database file: {tmpdir}/some/deep/internal/path.db"

                class _BoomConnection:
                    def execute(self, *args, **kwargs):
                        raise sqlite_error_cls(sensitive_detail)

                    def close(self):
                        pass

                import sqlite3 as _sqlite3
                sqlite_error_cls = _sqlite3.OperationalError

                with patch.object(database, "get_connection", return_value=_BoomConnection()):
                    report_text = database.generate_statistics_report()

                assert sensitive_detail not in report_text
                assert tmpdir not in report_text
                assert "unable to generate the report" in report_text.lower()


class TestBackupErrorSanitization:
    def test_backup_database_hides_raw_exception_on_failure(self):
        """Force shutil.copy2 to fail with a message containing a real path
        and confirm the user-facing message doesn't repeat it."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "attendance.db"
            db_path.write_bytes(b"SQLite format 3")

            sensitive_detail = f"Permission denied: '{tmpdir}/secret_internal_detail.db'"

            with patch.object(database, "DB_PATH", str(db_path)):
                with patch("core.database.shutil.copy2", side_effect=OSError(sensitive_detail)):
                    ok, msg, path = database.backup_database()

            assert ok is False
            assert path is None
            assert sensitive_detail not in msg
            assert tmpdir not in msg
            assert "backup failed" in msg.lower()


class TestStudentSaveErrorSanitization:
    def test_add_student_generic_integrity_error_is_sanitized(self):
        """Known constraint violations (fingerprint_id, student_no) still
        get their friendly, specific messages - but any other integrity
        error must fall back to a generic message, not raw sqlite text
        (which can reveal table/column names)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "attendance.db"
            with patch.object(database, "DB_PATH", str(db_path)):
                database.init_database()

                import sqlite3

                class _BoomConnection:
                    def execute(self, *args, **kwargs):
                        raise sqlite3.IntegrityError("NOT NULL constraint failed: students.grade")

                    def commit(self):
                        pass

                    def close(self):
                        pass

                with patch.object(database, "get_connection", return_value=_BoomConnection()):
                    ok, msg = database.add_student(1, "S-001", "Alice", "10", "A")

                assert ok is False
                assert "students.grade" not in msg
                assert "constraint" not in msg.lower()
                assert "check the application logs" in msg.lower()

    def test_add_student_known_constraint_still_gets_friendly_message(self):
        """Regression guard: the sanitization fix must not break the
        existing friendly messages for the two known, expected cases."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "attendance.db"
            with patch.object(database, "DB_PATH", str(db_path)):
                database.init_database()
                ok1, _ = database.add_student(5, "S-005", "Alice", "10", "A")
                assert ok1 is True

                ok2, msg2 = database.add_student(5, "S-006", "Bob", "10", "A")
                assert ok2 is False
                assert "already assigned" in msg2.lower()

                ok3, msg3 = database.add_student(6, "S-005", "Carol", "10", "A")
                assert ok3 is False
                assert "already exists" in msg3.lower()

    def test_update_student_generic_integrity_error_is_sanitized(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "attendance.db"
            with patch.object(database, "DB_PATH", str(db_path)):
                database.init_database()

                import sqlite3

                class _BoomConnection:
                    def execute(self, *args, **kwargs):
                        raise sqlite3.IntegrityError("NOT NULL constraint failed: students.section")

                    def commit(self):
                        pass

                    def close(self):
                        pass

                with patch.object(database, "get_connection", return_value=_BoomConnection()):
                    ok, msg = database.update_student(1, "S-001", "Alice", "10", "A")

                assert ok is False
                assert "students.section" not in msg
                assert "constraint" not in msg.lower()
                assert "check the application logs" in msg.lower()
