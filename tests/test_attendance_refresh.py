import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from gui.app import FingerprintApp


def test_schedule_attendance_refresh_uses_main_thread_callback():
    app = object.__new__(FingerprintApp)
    app._closing = False
    app.scheduled = []

    def fake_after(ms, callback, *args):
        app.scheduled.append((ms, callback, args))

    app.after = fake_after
    app._ui_ready = lambda: True

    app._schedule_attendance_refresh()

    assert len(app.scheduled) == 1
    assert app.scheduled[0][0] == 150
