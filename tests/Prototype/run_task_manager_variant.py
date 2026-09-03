"""Launch the Windows 11 Task Manager-inspired DSIS UI variant."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYTHON_DIR = ROOT / "Python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from task_manager_window import main


if __name__ == "__main__":
    main()
