import sys
from pathlib import Path
import tempfile
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOT = ROOT / "python"
sys.path.insert(0, str(PYTHON_ROOT))

import core.database as database
import core.permissions as permissions


def test_clear_all_data_clears_students_and_attendance():
    # clear_all_data() now enforces the "wipe" permission at the DB layer
    # (see SECURITY FIX note on the function) - pin the role explicitly so
    # this test is deterministic regardless of whatever role happens to be
    # saved in a real data/settings.json on disk.
    with mock.patch.object(permissions, "get_current_role", return_value="admin"):
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "test_attendance.db"
            with mock.patch.object(database, "DB_PATH", str(db_path)):
                database.init_database()
                success, _ = database.add_student(1, "S001", "Alice", "10", "A")
                assert success is True

                database.log_attendance(1, 95, "Present")
                database.log_attendance(1, 90, "Present")

                student_count, attendance_count = database.clear_all_data()

                assert student_count == 1
                assert attendance_count == 2
                assert database.get_all_students() == []
                assert database.get_attendance_all() == []
