import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOT = PROJECT_ROOT / "python"
import pytest

pytestmark = pytest.mark.unit
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))


class ProjectStructureTests(unittest.TestCase):
    def test_core_modules_import(self):
        import main
        import core.database as database
        import core.serial_handler as serial_handler
        import core.attendance as attendance

        self.assertTrue(hasattr(main, "main"))
        self.assertTrue(callable(database.init_database))
        self.assertTrue(hasattr(serial_handler, "SerialHandler"))
        self.assertTrue(hasattr(attendance, "AttendanceProcessor"))

    def test_v3_package_import_uses_canonical_entrypoint(self):
        import importlib
        import sys
        import types

        previous_webview = sys.modules.get("webview")
        webview_stub = types.ModuleType("webview")
        webview_stub.create_window = lambda *args, **kwargs: None
        webview_stub.start = lambda *args, **kwargs: None
        sys.modules["webview"] = webview_stub

        try:
            for name in [
                "python.gui_web.main_web",
                "python.gui_web.api",
                "gui_web.main_web",
                "gui_web.api",
            ]:
                sys.modules.pop(name, None)

            module = importlib.import_module("python.gui_web.main_web")
        finally:
            if previous_webview is None:
                sys.modules.pop("webview", None)
            else:
                sys.modules["webview"] = previous_webview

        self.assertTrue(hasattr(module, "main"))


if __name__ == "__main__":
    unittest.main()
