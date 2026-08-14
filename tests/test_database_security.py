"""Security tests for database module - path traversal and validation."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from core.database import restore_database


class TestRestoreDatabasePathTraversal:
    """Test that restore_database prevents path traversal attacks."""
    
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
            
            # Create a mock backup file
            backup_file = backups_dir / 'attendance_20240101.db'
            backup_file.write_bytes(b'SQLite format 3')
            
            # Create the original database file
            db_path.write_bytes(b'SQLite format 3')
            
            with patch('core.database.DB_PATH', str(db_path)):
                result_ok, result_msg = restore_database(str(backup_file))
                
                # Should succeed because the file is within backups directory
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
    
    def test_restore_database_sanitizes_error_messages(self):
        """Error messages should not expose full filesystem paths."""
        with patch('core.database.DB_PATH', '/app/data/attendance.db'):
            result_ok, result_msg = restore_database('../../../etc/passwd')
            
            # Error message should be generic, not exposing the attempted path
            assert not result_ok
            # The message should be informative but not expose internal paths
            assert 'Restore failed' in result_msg or 'Invalid' in result_msg
