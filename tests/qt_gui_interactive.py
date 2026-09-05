"""Launch the maintained Qt UI as an interactive smoke test.

This file works from the repository's tests folder and from the root of the
extracted interactive bundle. It intentionally leaves the UI disconnected so
screens and navigation can be tested without an Arduino.
"""

import sys
from pathlib import Path


def _runtime_root() -> Path:
    current = Path(__file__).resolve().parent
    candidates = (current, current.parent)
    for candidate in candidates:
        if (candidate / "python" / "gui_qt" / "main_qt.py").exists():
            return candidate
    raise RuntimeError("Could not find the Python runtime directory next to this launcher.")


ROOT = _runtime_root()
PYTHON_DIR = ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from gui_qt.main_qt import main  # pyright: ignore[reportMissingImports, reportUnknownVariableType]


if __name__ == "__main__":
    main()
