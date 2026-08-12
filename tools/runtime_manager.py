"""DSIS Runtime Manager

Small PySide6 GUI to detect a portable Python runtime, verify dependencies,
and optionally launch the portable interpreter to run DSIS or tests.

This tool is intentionally minimal and does not modify any global state.
It runs subprocesses against the portable interpreter when available.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import List

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QListWidget,
    QListWidgetItem,
    QHBoxLayout,
)


REPO_ROOT = Path(__file__).resolve().parent.parent
PORTABLE_PYTHON = REPO_ROOT / "system" / "python" / ("python.exe" if sys.platform.startswith("win") else "python")

RUNTIME_DEPS = [
    "PySide6",
    "serial",  # pyserial (import name `serial`)
    "Pillow",
    "matplotlib",
    "openpyxl",
]


def run_process(cmd: List[str], timeout: int = 60) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode, out.strip()
    except Exception as exc:
        return 1, str(exc)


class RuntimeManager(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("DSIS Runtime Manager")
        self.resize(720, 460)

        layout = QVBoxLayout(self)

        self.status_label = QLabel("Initializing...")
        layout.addWidget(self.status_label)

        # Runtime info
        info_row = QHBoxLayout()
        self.runtime_label = QLabel("Portable Python: unknown")
        info_row.addWidget(self.runtime_label)

        self.version_label = QLabel("")
        info_row.addWidget(self.version_label)
        layout.addLayout(info_row)

        # Dependency checklist
        layout.addWidget(QLabel("Dependencies to verify:"))
        self.deps_list = QListWidget()
        for pkg in RUNTIME_DEPS:
            item = QListWidgetItem(f"{pkg} — unknown")
            self.deps_list.addItem(item)
        layout.addWidget(self.deps_list)

        # Buttons
        btn_row = QHBoxLayout()
        self.check_env_btn = QPushButton("Check Environment")
        self.check_env_btn.clicked.connect(self.check_environment)
        btn_row.addWidget(self.check_env_btn)

        self.verify_deps_btn = QPushButton("Verify Dependencies")
        self.verify_deps_btn.clicked.connect(self.verify_dependencies)
        btn_row.addWidget(self.verify_deps_btn)

        self.run_dsis_btn = QPushButton("Run DSIS (portable)")
        self.run_dsis_btn.clicked.connect(self.run_dsis)
        btn_row.addWidget(self.run_dsis_btn)

        self.run_tests_btn = QPushButton("Run Tests (portable)")
        self.run_tests_btn.clicked.connect(self.run_tests)
        btn_row.addWidget(self.run_tests_btn)

        layout.addLayout(btn_row)

        layout.addWidget(QLabel("Command output:"))
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

        self.refresh_ui_initial()

    def refresh_ui_initial(self) -> None:
        exists = PORTABLE_PYTHON.exists()
        self.runtime_label.setText(f"Portable Python: {'detected' if exists else 'not found'}")
        if exists:
            rc, out = run_process([str(PORTABLE_PYTHON), "--version"])
            self.version_label.setText(out if out else "(unknown)")
        else:
            self.version_label.setText("")
        self.status_label.setText("Ready")

    def append_output(self, text: str) -> None:
        self.output.append(text)

    def check_environment(self) -> None:
        self.append_output("Checking portable runtime...")
        exists = PORTABLE_PYTHON.exists()
        if not exists:
            self.append_output(f"Portable interpreter not found at: {PORTABLE_PYTHON}")
            self.refresh_ui_initial()
            return

        rc, out = run_process([str(PORTABLE_PYTHON), "--version"])
        self.append_output(out or f"Exit code: {rc}")
        self.refresh_ui_initial()

    def verify_dependencies(self) -> None:
        self.append_output("Verifying dependencies using portable Python...")
        if not PORTABLE_PYTHON.exists():
            self.append_output("Portable Python not available. Run a bootstrap or place an embeddable Python in system/python/")
            return

        for i in range(self.deps_list.count()):
            item = self.deps_list.item(i)
            pkg = RUNTIME_DEPS[i]
            code = (
                "import importlib, json\n"
                f"pkg='{pkg}'\n"
                "try:\n"
                " m=importlib.import_module(pkg)\n"
                " v=getattr(m,'__version__', getattr(m,'VERSION', 'unknown'))\n"
                " print(json.dumps({'ok':True,'version':str(v)}))\n"
                "except Exception as e:\n"
                " print(json.dumps({'ok':False,'error':str(e)}))\n"
            )
            rc, out = run_process([str(PORTABLE_PYTHON), "-c", code])
            try:
                info = json.loads(out.splitlines()[-1]) if out else {"ok": False, "error": "no output"}
            except Exception:
                info = {"ok": False, "error": out}

            if info.get("ok"):
                item.setText(f"{pkg} — OK ({info.get('version')})")
            else:
                item.setText(f"{pkg} — MISSING ({info.get('error')})")
            self.append_output(f"{pkg}: {out}")

    def run_dsis(self) -> None:
        if not PORTABLE_PYTHON.exists():
            self.append_output("Cannot run DSIS: portable Python not found.")
            return
        script = REPO_ROOT / "run_qt_gui.py"
        if not script.exists():
            self.append_output(f"Launcher not found: {script}")
            return
        self.append_output(f"Launching DSIS with: {PORTABLE_PYTHON} {script}")
        # Launch without waiting so GUI can stay responsive; show output when done
        try:
            proc = subprocess.Popen([str(PORTABLE_PYTHON), str(script)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            out, _ = proc.communicate()
            self.append_output(out or f"Process exited with {proc.returncode}")
        except Exception as exc:
            self.append_output(str(exc))

    def run_tests(self) -> None:
        if not PORTABLE_PYTHON.exists():
            self.append_output("Cannot run tests: portable Python not found.")
            return
        self.append_output("Running pytest on portable Python (this may take a while)...")
        cmd = [str(PORTABLE_PYTHON), "-m", "pytest", "-q"]
        rc, out = run_process(cmd, timeout=600)
        self.append_output(out or f"Exit code: {rc}")


def main() -> None:
    app = QApplication.instance() or QApplication([])
    w = RuntimeManager()
    w.show()
    app.exec()


if __name__ == "__main__":
    main()
