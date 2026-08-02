from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QLabel
)
from PySide6.QtCore import Qt

from gui_qt.widgets.sidebar import Sidebar
from gui_qt.pages.dashboard_page import DashboardPage
from gui_qt.pages.attendance_page import AttendancePage
from gui_qt.pages.students_page import StudentsPage
from gui_qt.pages.reports_page import ReportsPage
from gui_qt.pages.logs_page import LogsPage
from gui_qt.pages.settings_page import SettingsPage
from gui_qt.workers.serial_worker import SerialWorker

PAGE_TITLES = {
    "dashboard": "Dashboard",
    "attendance": "Attendance",
    "students": "Students",
    "reports": "Reports",
    "logs": "Logs",
    "settings": "Settings",
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fingerprint Attendance System")
        self.resize(1180, 720)
        self.setMinimumSize(860, 560)

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- sidebar ----
        self.sidebar = Sidebar()
        self.sidebar.page_selected.connect(self.switch_page)
        root.addWidget(self.sidebar)

        # ---- right side: header + stacked pages ----
        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)

        header = QWidget()
        header.setObjectName("headerBar")
        header.setFixedHeight(56)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)

        self.page_title = QLabel("Dashboard")
        self.page_title.setObjectName("pageTitle")

        self.connection_label = QLabel("Disconnected")
        self.connection_label.setObjectName("connectionStatus")
        self.connection_label.setProperty("state", "disconnected")

        header_layout.addWidget(self.page_title)
        header_layout.addStretch()
        header_layout.addWidget(self.connection_label)

        right.addWidget(header)

        self.stack = QStackedWidget()
        self.dashboard_page = DashboardPage()
        self.attendance_page = AttendancePage()
        self.students_page = StudentsPage()
        self.reports_page = ReportsPage()
        self.logs_page = LogsPage()
        self.settings_page = SettingsPage()

        for page in (
            self.dashboard_page, self.attendance_page, self.students_page,
            self.reports_page, self.logs_page, self.settings_page,
        ):
            self.stack.addWidget(page)

        right.addWidget(self.stack)

        right_container = QWidget()
        right_container.setLayout(right)
        root.addWidget(right_container)

        self._page_index = {
            "dashboard": 0, "attendance": 1, "students": 2,
            "reports": 3, "logs": 4, "settings": 5,
        }

        # ---- serial worker ----
        # TODO: pull port/baud from settings_store instead of hardcoding
        self.serial_worker = SerialWorker(port="Auto-detect", baud=115200)
        self.serial_worker.connection_changed.connect(self.on_connection_changed)
        self.serial_worker.scan_event.connect(self.on_scan_event)
        self.serial_worker.log_line.connect(self.logs_page.append_line)
        self.serial_worker.error.connect(self.on_serial_error)
        self.serial_worker.start()

    def switch_page(self, key: str):
        self.stack.setCurrentIndex(self._page_index[key])
        self.page_title.setText(PAGE_TITLES[key])

    def on_connection_changed(self, state: str):
        labels = {
            "connected": "Connected",
            "disconnected": "Disconnected",
            "connecting": "Connecting…",
        }
        self.connection_label.setText(labels.get(state, state))
        self.connection_label.setProperty("state", state)
        # force stylesheet re-poll after dynamic property change
        self.connection_label.style().unpolish(self.connection_label)
        self.connection_label.style().polish(self.connection_label)

    def on_scan_event(self, event: dict):
        self.dashboard_page.on_scan_event(event)
        self.attendance_page.on_scan_event(event)

    def on_serial_error(self, message: str):
        self.logs_page.append_line(f"[ERROR] {message}")

    def closeEvent(self, event):
        self.serial_worker.stop()
        super().closeEvent(event)
