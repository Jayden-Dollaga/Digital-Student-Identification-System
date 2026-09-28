import ast
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOT = ROOT / "python"
ARCHIVED_MODULE_PARTS = {
    "archive",
    "legacy",
    "legacy_ui",
    "gui",
    "gui_qt",
    "v2_reference",
    "customtkinter",
    "pyside6",
    "pyqt5",
    "pyqt6",
    "tkinter",
}


def _active_v3_sources(root):
    python_root = root / "python"
    sources = [
        root / "run_web_gui.py",
        python_root / "startup_preflight.py",
        python_root / "config.py",
        python_root / "settings_store.py",
    ]
    for directory in ("gui_web", "core", "services"):
        sources.extend(
            path
            for path in (python_root / directory).rglob("*.py")
            if "v2_reference" not in path.parts
        )
    return sorted(path for path in sources if path.is_file())


def _imported_names(node):
    if isinstance(node, ast.Import):
        yield from (alias.name for alias in node.names)
        return

    if isinstance(node, ast.ImportFrom):
        if node.module:
            yield node.module
            for alias in node.names:
                if alias.name != "*":
                    yield f"{node.module}.{alias.name}"
        else:
            yield from (alias.name for alias in node.names if alias.name != "*")


def _archived_imports(sources):
    violations = []
    for path in sources:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            for name in _imported_names(node):
                parts = {part.casefold() for part in name.split(".")}
                if parts.intersection(ARCHIVED_MODULE_PARTS):
                    violations.append((path, node.lineno, name))
    return violations


def _assert_no_archived_imports(sources):
    violations = _archived_imports(sources)
    details = "; ".join(f"{path}:{line}: {name}" for path, line, name in violations)
    assert not violations, f"Active v3 sources import archived UI modules: {details}"


def test_guardrail_assertion_detects_a_planted_archived_import(tmp_path):
    active_copy = tmp_path / "python" / "gui_web" / "main_web.py"
    active_copy.parent.mkdir(parents=True)
    active_copy.write_text("from archive.legacy_ui.v1.python.gui import app\n", encoding="utf-8")

    with pytest.raises(AssertionError, match="archive.legacy_ui") as failure:
        _assert_no_archived_imports([active_copy])

    details = str(failure.value)
    assert "main_web.py:1: archive.legacy_ui.v1.python.gui.app" in details
    print(f"Expected planted-import assertion: {details}")


def test_active_v3_runtime_does_not_import_archived_ui_modules():
    _assert_no_archived_imports(_active_v3_sources(ROOT))