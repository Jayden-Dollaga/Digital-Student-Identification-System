"""Compatibility path for the archived Qt interface.

V3 is maintained under ``gui_web``. This package only exposes the archived Qt
modules to historical tests and launchers that still import ``gui_qt``.
"""

from pathlib import Path

_archived_qt = Path(__file__).resolve().parents[2] / "archive" / "legacy-ui" / "v2" / "python" / "gui_qt"
if _archived_qt.is_dir():
    __path__.append(str(_archived_qt))
