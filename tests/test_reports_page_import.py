import sys
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
PYTHON_DIR = PYTHON_ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))


def test_reports_page_can_import_database_helper():
    from core.database import get_daily_attendance_summary
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "legacy_reports_page",
        Path(__file__).resolve().parents[1] / "python" / "gui" / "legacy" / "reports_table_page.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert callable(get_daily_attendance_summary)
    assert hasattr(module, "ReportsPage")
