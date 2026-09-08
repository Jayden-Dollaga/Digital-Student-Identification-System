"""Compatibility package for archived GUI imports.

The maintained UI is under ``gui_web``. The archived Qt tests still import
modules from the historical ``gui`` package, so expose that package path when
it is present without restoring the archived implementation into the active UI.
"""

import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parents[2]
_archived_python_roots = {
    str(_project_root / "archive" / "legacy-ui" / "v1" / "python").casefold(),
    str(_project_root / "archive" / "legacy-ui" / "v2" / "python").casefold(),
}
sys.path[:] = [entry for entry in sys.path if str(entry).casefold() not in _archived_python_roots]

_archived_gui = _project_root / "archive" / "legacy-ui" / "v2" / "python" / "gui"
if _archived_gui.is_dir():
    __path__.append(str(_archived_gui))
