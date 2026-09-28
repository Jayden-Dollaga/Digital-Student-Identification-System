from pathlib import Path

from packaging.requirements import Requirement


ROOT = Path(__file__).resolve().parents[1]


def _requirement_names(filename):
    manifest = ROOT / filename
    names = set()
    for line in manifest.read_text(encoding="utf-8").splitlines():
        entry = line.strip()
        if not entry or entry.startswith("#"):
            continue
        if entry.startswith("-r "):
            names.update(_requirement_names(entry[3:].strip()))
        else:
            names.add(Requirement(entry).name.lower().replace("_", "-"))
    return names


def test_default_requirements_are_for_the_active_v3_runtime():
    runtime = _requirement_names("requirements.txt")

    assert {"pyserial", "cryptography", "pywebview"}.issubset(runtime)
    assert not runtime.intersection({"customtkinter", "pyside6", "pytest", "pytest-forked", "pyinstaller"})


def test_development_requirements_include_archived_ui_and_test_tools():
    development = _requirement_names("requirements-dev.txt")

    assert {"customtkinter", "pyside6", "pytest", "pytest-forked", "pyinstaller"}.issubset(development)