import runpy
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
python_root = project_root / "python"

if str(python_root) not in sys.path:
    sys.path.insert(0, str(python_root))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

archive_path = python_root / "testing_area" / "gui" / "legacy" / "bfeas_app2.py"
if not archive_path.exists():
    # This legacy script is retained for compatibility with older archived paths.
    # If the archive copy is absent, keep the import path robust instead of
    # crashing the application or the import harness.
    print(f"Legacy archive path not found: {archive_path}. Skipping legacy script execution.")
else:
    runpy.run_path(str(archive_path), run_name="__main__")
