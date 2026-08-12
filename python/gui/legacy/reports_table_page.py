import importlib.util
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
python_root = project_root / "python"

if str(python_root) not in sys.path:
    sys.path.insert(0, str(python_root))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

archive_path = python_root / "testing_area" / "gui" / "legacy" / "reports_table_page.py"
if not archive_path.exists():
    # Compatibility shim: legacy archive paths may not exist in the current repo.
    # Importing this module should remain non-fatal for tests and tooling.
    class ReportsPage:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    __all__ = ["ReportsPage"]
    print(f"Legacy archive path not found: {archive_path}. Using compatibility stub.")
else:
    spec = importlib.util.spec_from_file_location("testing_area_reports_table_page", archive_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    for name, value in vars(module).items():
        if not name.startswith("__"):
            globals()[name] = value
