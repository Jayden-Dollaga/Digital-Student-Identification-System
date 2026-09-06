"""Launch the active HTML/pywebview DSIS interface (v3) from the repository root."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYTHON_DIR = ROOT / "python"
GUI_WEB_DIR = PYTHON_DIR / "gui_web"

for path in (PYTHON_DIR, GUI_WEB_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from gui_web.main_web import main


if __name__ == "__main__":
    main()
