"""Launcher for the PySide6-based Qt interface.

This module is the entry point for the modern desktop UI. It loads the
stylesheet, creates the main window, and starts the Qt application loop.
It is intentionally separate from the legacy CustomTkinter interface so the
new UI can be tested and iterated without replacing the older workflow.
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

from gui_qt.main_window import MainWindow
from settings_store import load_settings


def load_stylesheet(app: QApplication, theme: str = "dark"):
    theme_file = "theme_light.qss" if theme.lower() == "light" else "theme.qss"
    qss_path = Path(__file__).parent / theme_file
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8", errors="replace"))
    elif theme.lower() == "light":
        app.setStyleSheet("")


def main():
    app = QApplication(sys.argv)
    settings = load_settings()
    load_stylesheet(app, settings.get("theme", "dark"))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
