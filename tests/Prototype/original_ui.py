"""Launch the standalone reconstruction of the original DSIS UI."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYTHON_DIR = ROOT / "Python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from original_window import main


if __name__ == "__main__":
    main()
