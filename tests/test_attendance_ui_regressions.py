import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from core import database as db_module
from gui.app import FingerprintApp


def test_start_scan_resets_mode_state(monkeypatch):
    app = object.__new__(FingerprintApp)
    app.enroll_dialog = None
    app.enroll_mode_active = True
    app.wipe_mode_active = True
    app.serial_handler = SimpleNamespace(connected=True, send_command=lambda command: True)
    app.log_message = lambda message: None
    app._set_scan_mode_ui = lambda: None

    FingerprintApp.start_scan(app)

    assert app.enroll_mode_active is False
    assert app.wipe_mode_active is False


def test_get_attendance_today_orders_newest_first(tmp_path):
    db_path = tmp_path / "attendance_test.db"
    db_module.DB_PATH = str(db_path)
    db_module.init_database()

    with db_module.get_connection() as conn:
        conn.execute(
            "INSERT INTO students (fingerprint_id, student_no, student_name, grade, section, enrollment_date, updated_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (1, "S-1", "Student One", "10", "A", "2026-07-17T09:00:00", "2026-07-17T09:00:00"),
        )
        conn.execute(
            "INSERT INTO students (fingerprint_id, student_no, student_name, grade, section, enrollment_date, updated_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (2, "S-2", "Student Two", "10", "A", "2026-07-17T09:00:00", "2026-07-17T09:00:00"),
        )
        conn.execute(
            "INSERT INTO attendance (fingerprint_id, date, time, confidence, status, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (1, "2026-07-17", "09:00:00", 100, "Present", "2026-07-17T09:00:00"),
        )
        conn.execute(
            "INSERT INTO attendance (fingerprint_id, date, time, confidence, status, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (2, "2026-07-17", "09:00:00", 100, "Present", "2026-07-17T09:00:00"),
        )
        conn.commit()

    rows = db_module.get_attendance_today()
    assert [row["fingerprint_id"] for row in rows[:2]] == [2, 1]
