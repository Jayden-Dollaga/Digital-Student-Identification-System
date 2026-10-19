"""Regression tests for attendance-query indexes created by schema initialization."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOT = ROOT / "python"
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from core import database


pytestmark = pytest.mark.integration


def test_attendance_composite_indexes_are_created_for_existing_database(tmp_path, monkeypatch):
    """Startup upgrades an existing database without requiring a manual migration."""
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "dsis-index-test.db"))

    database.init_database()
    conn = database.get_connection()
    try:
        indexes = {row["name"] for row in conn.execute("PRAGMA index_list(attendance)")}
    finally:
        conn.close()

    assert "idx_attendance_timestamp_id" in indexes
    assert "idx_attendance_date_time_timestamp" in indexes
    assert "idx_attendance_student_date_time" in indexes
