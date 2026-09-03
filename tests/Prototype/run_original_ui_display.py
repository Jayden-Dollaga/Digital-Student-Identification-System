"""Launch the display-only shell built from the real application UI pages."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYTHON_DIR = ROOT / "Python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from actual_ui_prototype import main


if __name__ == "__main__":
    main()
