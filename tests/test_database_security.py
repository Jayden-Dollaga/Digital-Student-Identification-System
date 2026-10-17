"""Security tests for database module - path traversal and validation."""

import sys
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from core.database import restore_database
from core import database



pytestmark = pytest.mark.integration


def create_valid_sqlite_db(path):
    connection = sqlite3.connect(path)
    try:
        connection.execute("CREATE TABLE validation_probe (value TEXT)")
        connection.commit()
    finally:
        connection.close()

def test_has_linked_rfid_cards_tracks_nonempty_card_links():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "attendance.db"
        with patch.object(database, "DB_PATH", str(db_path)):
            database.init_database()
            assert database.has_linked_rfid_cards() is False
            assert database.register_student(1, "LRN-001", "Alex Reyes", "12", "CSS")[0]
            assert database.has_linked_rfid_cards() is False

            ok, message = database.bind_student_card(1, "AA:BB:CC:DD")
            assert ok, message
            assert database.has_linked_rfid_cards() is True

            database.clear_student_card(1)
            assert database.has_linked_rfid_cards() is False


def test_daily_attendance_summary_prefers_good_match_over_older_weak_match():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "attendance.db"
        with patch.object(database, "DB_PATH", str(db_path)):
            database.init_database()
            assert database.register_student(1, "LRN-001", "Alex Reyes", "12", "CSS")[0]
            database.log_attendance(1, 80, "WEAK MATCH", datetime(2026, 10, 15, 8, 0, 0))
            database.log_attendance(1, 210, "GOOD MATCH", datetime(2026, 10, 15, 8, 5, 0))

            rows = database.get_daily_attendance_summary("2026-10-15", "2026-10-15")

        assert len(rows) == 1
        assert rows[0]["status"] == "GOOD MATCH"
        assert rows[0]["match_status"] == "GOOD MATCH"


def test_daily_attendance_summary_keeps_same_named_students_separate():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "attendance.db"
        with patch.object(database, "DB_PATH", str(db_path)):
            database.init_database()
            assert database.register_student(1, "LRN-001", "Alex Reyes", "12", "CSS")[0]
            assert database.register_student(2, "LRN-002", "Alex Reyes", "12", "CSS")[0]
            database.log_attendance(1, 180, "GOOD MATCH", datetime(2026, 10, 15, 8, 0, 0))
            database.log_attendance(2, 190, "GOOD MATCH", datetime(2026, 10, 15, 8, 1, 0))

            rows = database.get_daily_attendance_summary("2026-10-15", "2026-10-15")

        assert len(rows) == 2
        assert {row["student_no"] for row in rows} == {"LRN-001", "LRN-002"}
        assert {row["student_name"] for row in rows} == {"Alex Reyes"}


class TestRestoreDatabasePathTraversal:
    """Test that restore_database prevents path traversal attacks."""

    def test_backup_includes_committed_wal_records(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "attendance.db"
            source = __import__("sqlite3").connect(db_path)
            source.execute("PRAGMA journal_mode=WAL")
            source.execute("CREATE TABLE records (value TEXT)")
            source.execute("INSERT INTO records VALUES (?)", ("committed",))
            source.commit()
            assert Path(str(db_path) + "-wal").exists()

            with patch.object(database, "DB_PATH", str(db_path)):
                success, _message, backup_path = database.backup_database()

            source.close()
            assert success is True
            restored = __import__("sqlite3").connect(backup_path)
            try:
                assert restored.execute("SELECT value FROM records").fetchall() == [("committed",)]
            finally:
                restored.close()

    def test_connection_enables_wal_and_busy_timeout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "attendance.db"
            with patch.object(database, "DB_PATH", str(db_path)):
                with database.get_connection() as connection:
                    assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
                    assert connection.execute("PRAGMA busy_timeout").fetchone()[0] == 5000
                    assert connection.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
    
    def test_restore_database_rejects_paths_outside_backups_dir(self):
        """Path traversal attack should be rejected."""
        # Try to restore from a path outside the backups directory
        with patch('core.database.DB_PATH', '/app/data/attendance.db'):
            # Attempt to access parent directories
            result_ok, result_msg = restore_database('../../../etc/passwd')
            
            assert not result_ok
            assert 'Invalid backup file location' in result_msg or 'outside backups' in result_msg.lower()
    
    def test_restore_database_rejects_absolute_paths_outside_backups(self):
        """Absolute paths outside backups dir should be rejected."""
        with patch('core.database.DB_PATH', '/app/data/attendance.db'):
            result_ok, result_msg = restore_database('/etc/passwd')
            
            assert not result_ok
            assert 'Invalid backup file location' in result_msg or 'outside backups' in result_msg.lower()
    
    def test_restore_database_accepts_valid_backup_in_backups_dir(self):
        """Valid backup files in backups directory should be accepted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            db_path = tmpdir / 'attendance.db'
            backups_dir = tmpdir / 'backups'
            backups_dir.mkdir()

            backup_file = backups_dir / 'attendance_20240101.db'
            create_valid_sqlite_db(backup_file)
            create_valid_sqlite_db(db_path)

            with patch('core.database.DB_PATH', str(db_path)):
                result_ok, result_msg = restore_database(str(backup_file))

                assert result_ok
                assert 'successfully' in result_msg.lower()
    
    def test_restore_database_rejects_nonexistent_files(self):
        """Non-existent files should be rejected."""
        result_ok, result_msg = restore_database('/nonexistent/path/to/backup.db')
        
        assert not result_ok
        assert 'not found' in result_msg.lower() or 'invalid' in result_msg.lower()
    
    def test_restore_database_rejects_wrong_file_type(self):
        """Non-.db files should be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            db_path = tmpdir / 'attendance.db'
            backups_dir = tmpdir / 'backups'
            backups_dir.mkdir()
            
            # Create a non-.db file in backups
            non_db_file = backups_dir / 'somefile.txt'
            non_db_file.write_text('not a database')
            
            db_path.write_bytes(b'SQLite format 3')
            
            with patch('core.database.DB_PATH', str(db_path)):
                result_ok, result_msg = restore_database(str(non_db_file))
                
                # Should fail because it's not a .db file
                assert not result_ok
                assert 'file type' in result_msg.lower() or '.db' in result_msg

    def test_restore_database_rejects_tampered_db_file_with_invalid_sqlite_header(self):
        """A .db file that is not actually a SQLite database must be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            db_path = tmpdir / 'attendance.db'
            backups_dir = tmpdir / 'backups'
            backups_dir.mkdir()

            tampered_backup = backups_dir / 'attendance_tampered.db'
            tampered_backup.write_bytes(b'SQLite format 3\x00' + b'\x00' * 32)
            create_valid_sqlite_db(db_path)

            with patch('core.database.DB_PATH', str(db_path)):
                result_ok, result_msg = restore_database(str(tampered_backup))

                assert not result_ok
                assert 'invalid backup file' in result_msg.lower() or 'not a valid sqlite' in result_msg.lower()
    
    def test_restore_database_sanitizes_error_messages(self):
        """Error messages should not expose full filesystem paths."""
        with patch('core.database.DB_PATH', '/app/data/attendance.db'):
            result_ok, result_msg = restore_database('../../../etc/passwd')
            
            # Error message should be generic, not exposing the attempted path
            assert not result_ok
            # The message should be informative but not expose internal paths
            assert 'Restore failed' in result_msg or 'Invalid' in result_msg

    def test_restore_database_rejects_sibling_directory_with_similar_name(self):
        """This is the specific bug being fixed: a string-prefix check like
        str(backup_file).startswith(str(backup_dir)) would incorrectly accept
        a *sibling* directory such as "backups_evil" just because the string
        "backups" is a prefix of "backups_evil" - even though it is not
        actually inside the backups directory at all."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            db_path = tmpdir / 'attendance.db'
            backups_dir = tmpdir / 'backups'
            backups_dir.mkdir()
            evil_dir = tmpdir / 'backups_evil'
            evil_dir.mkdir()

            evil_file = evil_dir / 'attendance_20240101.db'
            evil_file.write_bytes(b'SQLite format 3')
            db_path.write_bytes(b'SQLite format 3')

            with patch('core.database.DB_PATH', str(db_path)):
                result_ok, result_msg = restore_database(str(evil_file))

                assert not result_ok
                assert 'Invalid backup file location' in result_msg or 'outside backups' in result_msg.lower()

    def test_restore_database_accepts_nested_backup_subdirectory(self):
        """A genuinely nested subdirectory inside backups/ should still work -
        the fix must not be so strict it breaks legitimate nested backups."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            db_path = tmpdir / 'attendance.db'
            backups_dir = tmpdir / 'backups'
            nested_dir = backups_dir / '2026' / '08'
            nested_dir.mkdir(parents=True)

            backup_file = nested_dir / 'attendance_20260817.db'
            create_valid_sqlite_db(backup_file)
            create_valid_sqlite_db(db_path)

            with patch('core.database.DB_PATH', str(db_path)):
                result_ok, result_msg = restore_database(str(backup_file))

                assert result_ok
                assert 'successfully' in result_msg.lower()


class TestClearAllDataAuthorizationBoundary:
    """clear_all_data() is the actual destructive operation behind the wipe
    workflow. It used to have no authorization awareness of its own - only
    the UI call path (WipeDialog -> cmd_wipe()) was gated. These tests prove
    the permission check now lives at the operation itself, so it can't be
    bypassed by a different, unguarded caller."""

    def test_clear_all_data_blocked_for_role_without_wipe_permission(self):
        import core.permissions as permissions

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / 'attendance.db'
            with patch('core.database.DB_PATH', str(db_path)):
                import core.database as database
                database.init_database()
                database.add_student(1, 'S001', 'Alice', '10', 'A')

                with patch.object(permissions, 'get_current_role', return_value='guest'):
                    with pytest.raises(PermissionError):
                        database.clear_all_data()

                # Nothing should have been deleted - the guard must fire
                # before any DELETE statement runs, not after.
                assert len(database.get_all_students()) == 1

    def test_clear_all_data_blocked_for_unknown_role(self):
        """Fail closed: an unrecognized role must not be treated as authorized."""
        import core.permissions as permissions

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / 'attendance.db'
            with patch('core.database.DB_PATH', str(db_path)):
                import core.database as database
                database.init_database()
                database.add_student(1, 'S001', 'Alice', '10', 'A')

                with patch.object(permissions, 'get_current_role', return_value='not-a-real-role'):
                    with pytest.raises(PermissionError):
                        database.clear_all_data()

                assert len(database.get_all_students()) == 1

    def test_clear_all_data_succeeds_for_admin_role(self):
        """The protected wipe workflow must still work end to end for an
        authorized role - the fix must not just block everything."""
        import core.permissions as permissions

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / 'attendance.db'
            with patch('core.database.DB_PATH', str(db_path)):
                import core.database as database
                database.init_database()
                database.add_student(1, 'S001', 'Alice', '10', 'A')
                database.log_attendance(1, 95, 'Present')

                with patch.object(permissions, 'get_current_role', return_value='admin'):
                    student_count, attendance_count = database.clear_all_data()

                assert student_count == 1
                assert attendance_count == 1
                assert database.get_all_students() == []

    def test_clear_all_data_cannot_be_bypassed_by_calling_it_directly(self):
        """This is the exact scenario the fix closes: calling clear_all_data()
        directly (skipping cmd_wipe() / the WipeDialog entirely) must still
        respect the permission boundary, because the check now lives in
        clear_all_data() itself rather than only in its one known caller."""
        import core.permissions as permissions

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / 'attendance.db'
            with patch('core.database.DB_PATH', str(db_path)):
                import core.database as database
                database.init_database()
                database.add_student(1, 'S001', 'Alice', '10', 'A')

                # Call the raw database function directly - no cmd_wipe(),
                # no WipeDialog, no UI in the picture at all.
                with patch.object(permissions, 'get_current_role', return_value='teacher'):
                    with pytest.raises(PermissionError):
                        database.clear_all_data()

                assert len(database.get_all_students()) == 1


class TestDeleteStudentAuthorizationBoundary:
    """delete_student() is the actual destructive database operation behind
    student deletion in both the Qt and legacy GUIs. It used to have no
    authorization awareness of its own: the Qt page called it unconditionally
    before even checking whether the permission-gated cmd_delete() (the
    ESP32-side deletion) succeeded, and the legacy GUI only ran cmd_delete()
    at all when a device happened to be connected - so a disconnected
    session skipped permission checking entirely. These tests prove the
    check now lives at the operation itself."""

    def test_delete_student_blocked_for_role_without_delete_permission(self):
        import core.permissions as permissions

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / 'attendance.db'
            with patch('core.database.DB_PATH', str(db_path)):
                import core.database as database
                database.init_database()
                database.add_student(1, 'S001', 'Alice', '10', 'A')

                with patch.object(permissions, 'get_current_role', return_value='guest'):
                    with pytest.raises(PermissionError):
                        database.delete_student(1)

                assert len(database.get_all_students()) == 1

    def test_delete_student_blocked_when_device_not_connected(self):
        """This is the specific gap in the legacy GUI: it only checked
        permission via cmd_delete() when a device happened to be connected.
        A disconnected session must still be blocked at the DB layer."""
        import core.permissions as permissions

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / 'attendance.db'
            with patch('core.database.DB_PATH', str(db_path)):
                import core.database as database
                database.init_database()
                database.add_student(1, 'S001', 'Alice', '10', 'A')

                # No serial handler, no cmd_delete() call anywhere - just the
                # raw database function, the way it would be reached if the
                # device were disconnected.
                with patch.object(permissions, 'get_current_role', return_value='teacher'):
                    with pytest.raises(PermissionError):
                        database.delete_student(1)

                assert len(database.get_all_students()) == 1

    def test_delete_student_succeeds_for_admin_role(self):
        """The protected delete workflow must still work for an authorized role."""
        import core.permissions as permissions

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / 'attendance.db'
            with patch('core.database.DB_PATH', str(db_path)):
                import core.database as database
                database.init_database()
                database.add_student(1, 'S001', 'Alice', '10', 'A')

                with patch.object(permissions, 'get_current_role', return_value='admin'):
                    database.delete_student(1)

                assert database.get_all_students() == []
