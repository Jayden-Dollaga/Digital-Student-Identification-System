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
    raise FileNotFoundError(archive_path)

runpy.run_path(str(archive_path), run_name="__main__")
