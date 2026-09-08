"""Stable import paths for active and archived test fixtures."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATHS = (
    ROOT / "python",
    ROOT / "tests" / "Prototype" / "Python",
)

for path in reversed(PATHS):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)
