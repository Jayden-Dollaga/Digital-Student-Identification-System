"""Display-only shell composed from the application's real Qt pages.

This is a safe visual prototype: it uses the production page and sidebar
classes, but supplies preview-only serial objects and never starts hardware
workers or sends commands.
"""

import sys
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMainWindow, QStackedWidget, QVBoxLayout, QWidget

ROOT = Path(__file__).resolve().parents[3]
PYTHON_DIR = ROOT / "python"
if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from core.database import init_database
from gui_qt.main_qt import apply_base_style, apply_theme
from gui_qt.pages.attendance_page import AttendancePage
from gui_qt.pages.dashboard_page import DashboardPage
from gui_qt.pages.logs_page import LogsPage
from gui_qt.pages.reports_page import ReportsPage
from gui_qt.pages.settings_page import SettingsPage
from gui_qt.pages.students_page import StudentsPage
from gui_qt.widgets.sidebar import Sidebar


class PreviewSerialHandler:
    auto_reconnect_enabled = False

    def is_connected(self):
        return False

    def list_available_ports(self):
        return []


class PreviewSerialWorker(QObject):
    """Signal-compatible placeholder required by StudentsPage dialogs."""

    enroll_progress = Signal(str)
    raw_line = Signal(str)
    wipe_progress = Signal(str)
    delete_progress = Signal(str)


class ActualUIPrototypeWindow(QMainWindow):
    PAGE_TITLES = {
        "dashboard": "Dashboard",
        "attendance": "Attendance",
        "students": "Students",
        "reports": "Reports",
        "logs": "Logs",
        "settings": "Settings",
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DSIS Original UI - Display Prototype")
        self.resize(1180, 720)
        self.setMinimumSize(860, 560)
        self.serial_handler = PreviewSerialHandler()
        self.serial_worker = PreviewSerialWorker()
        init_database()

        root = QWidget()
        root.setObjectName("centralWidget")
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.page_selected.connect(self.switch_page)
        root_layout.addWidget(self.sidebar)

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        header = QWidget()
        header.setObjectName("headerBar")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)
        self.page_title = QLabel("Dashboard")
        self.page_title.setObjectName("pageTitle")
        header_layout.addWidget(self.page_title)
        header_layout.addStretch()
        self.preview_status = QLabel("Preview mode - hardware disconnected")
        self.preview_status.setObjectName("connectionStatus")
        self.preview_status.setProperty("state", "disconnected")
        header_layout.addWidget(self.preview_status)
        right.addWidget(header)

        self.stack = QStackedWidget()
        self._pages = {
            "dashboard": DashboardPage(),
            "attendance": AttendancePage(),
            "students": StudentsPage(self.serial_handler, self.serial_worker),
            "reports": ReportsPage(),
            "logs": LogsPage(self.serial_handler),
            "settings": SettingsPage(self.serial_handler),
        }
        for page in self._pages.values():
            self.stack.addWidget(page)
        right.addWidget(self.stack)

        right_widget = QWidget()
        right_widget.setLayout(right)
        root_layout.addWidget(right_widget, 1)

    def switch_page(self, key):
        if key not in self._pages:
            return
        self.stack.setCurrentWidget(self._pages[key])
        self.page_title.setText(self.PAGE_TITLES[key])
        page = self._pages[key]
        if hasattr(page, "refresh"):
            page.refresh()


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    apply_base_style(app)
    apply_theme(app, "dark")
    window = ActualUIPrototypeWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    main()
