"""Regression tests for recent-attendance pagination boundaries."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from core import database
from gui_web import api as api_module
from settings_store import default_settings

pytestmark = pytest.mark.unit


def _rows(count):
    return [
        {
            "fingerprint_id": index + 1,
            "student_no": f"S-{index + 1:03d}",
            "student_name": "Student",
            "grade": "12",
            "section": "A",
            "date": "2026-10-19",
            "time": "08:00:00",
            "status": "PRESENT",
            "event_type": "time_in",
        }
        for index in range(count)
    ]


@pytest.mark.parametrize(
    ("total_rows", "expected_rows", "expected_has_more"),
    [(99, 99, False), (100, 100, False), (101, 100, True), (205, 100, True)],
)
def test_recent_attendance_pagination_uses_lookahead(
    monkeypatch, total_rows, expected_rows, expected_has_more
):
    api = api_module.Api.__new__(api_module.Api)
    source_rows = _rows(total_rows)
    calls = []

    def get_page(limit, offset):
        calls.append((limit, offset))
        return source_rows[offset : offset + limit]

    monkeypatch.setattr(api_module.permissions, "has_permission", lambda action: True)
    monkeypatch.setattr(api_module.db, "get_attendance_paginated", get_page)
    monkeypatch.setattr(api_module, "load_settings", default_settings)

    result = api.get_attendance("recent", 0)

    assert len(result["rows"]) == expected_rows
    assert result["has_more"] is expected_has_more
    assert result["offset"] == 0
    assert calls == [(101, 0)]


@pytest.mark.parametrize("bad_offset", [-100, "not-an-offset", None, 1.5])
def test_recent_attendance_pagination_normalizes_untrusted_offset(monkeypatch, bad_offset):
    api = api_module.Api.__new__(api_module.Api)
    calls = []

    def get_page(limit, offset):
        calls.append((limit, offset))
        return []

    monkeypatch.setattr(api_module.permissions, "has_permission", lambda action: True)
    monkeypatch.setattr(api_module.db, "get_attendance_paginated", get_page)
    monkeypatch.setattr(api_module, "load_settings", default_settings)

    result = api.get_attendance("recent", bad_offset)

    assert result["offset"] == 0
    assert calls == [(101, 0)]


def test_last30_attendance_is_paginated_and_date_limited(monkeypatch):
    api = api_module.Api.__new__(api_module.Api)
    source_rows = _rows(205)
    calls = []

    def get_page(limit, offset, start_date=None, end_date=None):
        calls.append((limit, offset, start_date, end_date))
        return source_rows[offset : offset + limit]

    monkeypatch.setattr(api_module.permissions, "has_permission", lambda action: True)
    monkeypatch.setattr(api_module.db, "get_attendance_paginated", get_page)
    monkeypatch.setattr(api_module, "load_settings", default_settings)

    result = api.get_attendance("last30", 100)

    assert len(result["rows"]) == 100
    assert result["has_more"] is True
    assert result["offset"] == 100
    assert calls[0][0:2] == (101, 100)
    assert calls[0][2] <= calls[0][3]


def test_database_pagination_applies_inclusive_date_filters(tmp_path, monkeypatch):
    from datetime import datetime

    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "attendance.db"))
    database.init_database()
    ok, message = database.add_student(1, "S-001", "Student One", "12", "A")
    assert ok, message

    database.log_attendance(1, 200, "PRESENT", datetime(2026, 10, 5, 8, 0))
    database.log_attendance(1, 200, "PRESENT", datetime(2026, 10, 19, 8, 0))
    database.log_attendance(1, 200, "PRESENT", datetime(2026, 10, 24, 8, 0))

    rows = database.get_attendance_paginated(
        limit=10, offset=0, start_date="2026-10-10", end_date="2026-10-20"
    )

    assert [row["date"] for row in rows] == ["2026-10-19"]
