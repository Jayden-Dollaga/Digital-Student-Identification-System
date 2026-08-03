"""
New entry point for the PySide6 redesign.

Keep your existing main.py (ESP32 connect, DB init, CLI handling) as-is
for now — this file is a parallel entry point so you can run the new UI
without ripping out the working CustomTkinter app until you're ready to
switch over. Once you're happy with the redesign, point your
build_portable.bat / fingerprint_portable.spec at this file instead.
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

from gui_qt.main_window import MainWindow


def load_stylesheet(app: QApplication):
    qss_path = Path(__file__).parent / "theme.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text())


def main():
    app = QApplication(sys.argv)
    load_stylesheet(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
