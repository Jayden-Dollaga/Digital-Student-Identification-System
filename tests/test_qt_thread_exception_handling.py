import sys
import types
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOT = PROJECT_ROOT / "python"
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from gui_qt import main_qt


def test_handle_thread_exception_without_thread(monkeypatch):
    captured = {}

    def fake_exception(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(main_qt.log, "exception", fake_exception)

    args = types.SimpleNamespace(
        thread=None,
        exc_type=RuntimeError,
        exc_value=RuntimeError("boom"),
        exc_traceback=None,
    )

    main_qt._handle_thread_exception(args)

    assert "error" in captured["kwargs"]
    assert captured["kwargs"]["error"] == "boom"
