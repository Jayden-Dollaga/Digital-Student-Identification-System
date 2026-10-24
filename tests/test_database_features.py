import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

import pytest

from core import database

pytestmark = pytest.mark.unit


def test_clear_all_students_removes_all_profiles(tmp_path, monkeypatch):
    # Never let a destructive reset test touch the user's real attendance DB.
    test_db = tmp_path / "attendance.db"
    monkeypatch.setattr(database, "DB_PATH", str(test_db))
    database.init_database()

    # Fingerprint IDs must match the AS608's supported 1-127 range. Assert
    # registration succeeds so the test cannot pass because of leftover rows.
    success, message = database.add_student(5, "TEST-001", "Test User", "12", "A")
    assert success, message
    assert database.get_student(5) is not None

    cleared = database.clear_all_students()

    assert cleared >= 1
    assert database.get_student_count() == 0
    assert database.get_student(5) is None
