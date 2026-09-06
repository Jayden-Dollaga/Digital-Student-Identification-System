import importlib.util
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]
python_root = project_root / "python"

if str(python_root) not in sys.path:
    sys.path.insert(0, str(python_root))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# SECURITY: Legacy module loader with path validation
# This module dynamically loads legacy code only from the project directory.
# Path traversal is prevented by validating the resolved path is within the project.
archive_path = python_root / "testing_area" / "gui" / "legacy" / "reports_table_page.py"


def _is_safe_path(target_path: Path, allowed_root: Path) -> bool:
    """Check if target_path is within allowed_root (prevent path traversal)."""
    try:
        target_resolved = target_path.resolve()
        root_resolved = allowed_root.resolve()
        return str(target_resolved).startswith(str(root_resolved))
    except (ValueError, RuntimeError):
        return False


# Validate path is within project before attempting to load
if not _is_safe_path(archive_path, project_root):
    # Path traversal attempt detected - use stub class
    class ReportsPage:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    __all__ = ["ReportsPage"]
    print(f"Legacy archive path validation failed: {archive_path}. Using compatibility stub.")
elif not archive_path.exists():
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
