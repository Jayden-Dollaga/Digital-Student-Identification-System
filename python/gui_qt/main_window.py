import logging
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QLabel, QPushButton
)

import threading
from core.commands import cmd_scan, cmd_stop
from core.logger import AppFormatter, LOG, log
from gui_qt.widgets.sidebar import Sidebar
from gui_qt.pages.dashboard_page import DashboardPage
from gui_qt.pages.attendance_page import AttendancePage
from gui_qt.pages.students_page import StudentsPage
from gui_qt.pages.reports_page import ReportsPage
from gui_qt.pages.logs_page import LogsPage
from gui_qt.pages.settings_page import SettingsPage
from gui_qt.workers.serial_worker import SerialWorker

from core.database import init_database
from core.serial_handler import SerialHandler
from core.attendance import AttendanceProcessor
from config import get_default_com_port, get_config
from settings_store import load_settings

CONFIG = get_config()

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
        LOG.info("MainWindow initialization started")
        self.setWindowTitle("Fingerprint Attendance System")
        self.resize(1180, 720)
        self.setMinimumSize(860, 560)

        init_database()

        self.settings = load_settings()
        self.serial_handler = SerialHandler()
        self.serial_handler.auto_reconnect_enabled = bool(self.settings.get("auto_reconnect", True))
        self.auto_detect_serial = bool(self.settings.get("auto_detect_serial", True))
        self.attendance_processor = AttendanceProcessor()

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

        self.device_info_label = QLabel("No device metadata available")
        self.device_info_label.setObjectName("deviceInfoLabel")
        self.device_info_label.setStyleSheet("font-size: 11px; color: #AEB4BD;")

        self.connect_button = QPushButton("Connect")
        self.connect_button.setObjectName("primaryButton")
        self.connect_button.clicked.connect(self.on_connect_clicked)

        self.scan_toggle_button = QPushButton("SCAN")
        self.scan_toggle_button.setObjectName("secondaryButton")
        self.scan_toggle_button.clicked.connect(self.on_scan_toggle_clicked)
        self.scan_toggle_button.setEnabled(False)

        self.scan_active = False

        metadata_layout = QVBoxLayout()
        metadata_layout.setContentsMargins(0, 0, 0, 0)
        metadata_layout.setSpacing(4)
        metadata_layout.addWidget(self.connection_label)
        metadata_layout.addWidget(self.device_info_label)

        header_layout.addWidget(self.page_title)
        header_layout.addStretch()
        header_layout.addLayout(metadata_layout)
        header_layout.addSpacing(12)
        header_layout.addWidget(self.scan_toggle_button)
        header_layout.addSpacing(8)
        header_layout.addWidget(self.connect_button)

        right.addWidget(header)

        self.stack = QStackedWidget()
        self.dashboard_page = DashboardPage()
        self.attendance_page = AttendancePage()
        self.serial_worker = SerialWorker(self.serial_handler, self.attendance_processor)
        self.students_page = StudentsPage(serial_handler=self.serial_handler, serial_worker=self.serial_worker)
        self.reports_page = ReportsPage()
        self.logs_page = LogsPage(serial_handler=self.serial_handler)
        self.settings_page = SettingsPage(
            serial_handler=self.serial_handler,
            settings=self.settings,
            on_connection_settings_changed=self.on_connection_settings_changed,
        )

        self._pages = {
            "dashboard": self.dashboard_page,
            "attendance": self.attendance_page,
            "students": self.students_page,
            "reports": self.reports_page,
            "logs": self.logs_page,
            "settings": self.settings_page,
        }
        for page in self._pages.values():
            self.stack.addWidget(page)

        right.addWidget(self.stack)

        right_container = QWidget()
        right_container.setLayout(right)
        root.addWidget(right_container)

        self._page_order = list(self._pages.keys())

        # ---- serial worker (created earlier so StudentsPage's enroll/wipe
        #      dialogs can subscribe to its signals; starts polling now —
        #      actual connect happens when the user clicks Connect, same as
        #      app.py's toggle_connection -> start_reader_thread flow) ----
        self.serial_worker.connection_changed.connect(self.on_connection_changed)
        self.serial_worker.mode_changed.connect(self.on_scan_mode_changed)
        self.serial_worker.scan_event.connect(self.on_scan_event)
        self.serial_worker.raw_line.connect(self.logs_page.append_line)
        self.serial_worker.error.connect(self.on_serial_error)

        self._log_handler = self._create_log_handler()
        LOG.addHandler(self._log_handler)
        thread_name = (
            self.serial_worker.currentThread().objectName()
            if self.serial_worker.currentThread()
            else "unknown"
        )
        LOG.info("Starting SerialWorker | thread_name=%s", thread_name)
        self.serial_worker.start()
        LOG.info("SerialWorker started | thread_name=%s", thread_name)

    def switch_page(self, key: str):
        self.stack.setCurrentWidget(self._pages[key])
        self.page_title.setText(PAGE_TITLES[key])
        # refresh data-driven pages whenever the user navigates to them
        page = self._pages[key]
        if hasattr(page, "refresh"):
            page.refresh()

    def on_connect_clicked(self):
        if self.serial_handler.is_connected():
            self.serial_handler.disconnect()
            self.connect_button.setText("Connect")
            self.update_connection_metadata()
            self.logs_page.set_connection_state("disconnected")
            return

        saved_port = self.settings.get("com_port") or ""
        port = saved_port or get_default_com_port(CONFIG.com_port)
        baud = int(self.settings.get("baud_rate") or 115200)
        ok, msg = self.serial_handler.connect(port, baud, auto_detect=self.auto_detect_serial)
        if ok:
            self.connect_button.setText("Disconnect")
            self.settings["com_port"] = self.serial_handler.reconnect_port or port
            self.settings["baud_rate"] = baud
            self.update_connection_metadata()
            self.logs_page.set_connection_info(self.serial_handler.reconnect_port or port, baud)
            self.logs_page.set_connection_state("connected")
            LOG.info(
                "Connected to %s at %s baud. Device: %s",
                self.serial_handler.reconnect_port or port,
                baud,
                self.device_info_label.text(),
            )
        else:
            LOG.error("Connection failed: %s", msg)
            self.update_connection_metadata()
            self.logs_page.set_connection_state("disconnected")

    def _attempt_startup_connection(self):
        saved_port = self.settings.get("com_port") or ""
        port = saved_port or get_default_com_port(CONFIG.com_port)
        baud = int(self.settings.get("baud_rate") or CONFIG.baud_rate)
        ok, msg = self.serial_handler.connect(port, baud, auto_detect=self.auto_detect_serial)
        if ok:
            LOG.info(
                "Auto-connected to %s at %s baud. Device: %s",
                self.serial_handler.reconnect_port or port,
                baud,
                self.device_info_label.text(),
            )
            self.settings["com_port"] = self.serial_handler.reconnect_port or port
            self.update_connection_metadata()
        else:
            LOG.warning("Auto-connect failed: %s", msg)
            self.update_connection_metadata()

    def on_connection_settings_changed(
        self,
        port: str,
        baud: int,
        auto_reconnect: Optional[bool] = None,
        auto_detect: Optional[bool] = None,
        theme: Optional[str] = None,
    ):
        """Called by SettingsPage after Save — reconnect with new values if already connected."""
        self.settings["com_port"] = port
        self.settings["baud_rate"] = baud
        if auto_reconnect is not None:
            self.serial_handler.auto_reconnect_enabled = bool(auto_reconnect)
            self.settings["auto_reconnect"] = self.serial_handler.auto_reconnect_enabled
        if auto_detect is not None:
            self.auto_detect_serial = bool(auto_detect)
            self.settings["auto_detect_serial"] = self.auto_detect_serial
        if theme is not None:
            self.settings["theme"] = theme

        if self.serial_handler.is_connected():
            self.serial_handler.disconnect()
            ok, msg = self.serial_handler.connect(port, baud)
            if not ok:
                LOG.error("Reconnect failed: %s", msg)

    class _QtLogHandler(logging.Handler):
        def __init__(self, log_page):
            super().__init__()
            self.log_page = log_page
            self.setFormatter(AppFormatter("%(asctime)s | %(levelname)-7s | %(source)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S.%f"))

        def emit(self, record):
            try:
                self.log_page.append_record(record)
            except Exception:
                pass

    def _create_log_handler(self):
        handler = self._QtLogHandler(self.logs_page)
        handler.setLevel(getattr(logging, CONFIG.log_level.upper(), logging.INFO))
        return handler

    def on_connection_changed(self, state: str):
        labels = {
            "connected": "Connected",
            "disconnected": "Disconnected",
            "connecting": "Connecting…",
        }
        self.connection_label.setText(labels.get(state, state))
        self.connection_label.setProperty("state", state)
        self.connection_label.style().unpolish(self.connection_label)
        self.connection_label.style().polish(self.connection_label)
        self.connect_button.setText("Disconnect" if state in {"connected", "connecting"} else "Connect")
        self.scan_toggle_button.setEnabled(state == "connected")
        if not state == "connected":
            self.scan_active = False
            self._update_scan_toggle_button()
        self.logs_page.set_connection_state(state)
        if state == "connected":
            self.logs_page.set_connection_info(self.serial_handler.reconnect_port or "N/A", self.serial_handler.reconnect_baud or 0)
        self.update_connection_metadata()

    def on_scan_event(self, event: dict):
        self.dashboard_page.on_scan_event(event)
        self.attendance_page.on_scan_event(event)

    def on_serial_error(self, message: str):
        LOG.error("Serial error: %s", message)

    def on_scan_mode_changed(self, mode: str):
        if mode == "scan":
            self.scan_active = True
        elif mode == "command":
            self.scan_active = False
        self._update_scan_toggle_button()

    def _update_scan_toggle_button(self):
        if self.scan_active:
            self.scan_toggle_button.setText("STOP")
            self.scan_toggle_button.setStyleSheet("background-color: #E74C3C; color: white;")
        else:
            self.scan_toggle_button.setText("SCAN")
            self.scan_toggle_button.setStyleSheet("")

    def on_scan_toggle_clicked(self):
        if not self.serial_handler.is_connected():
            LOG.warning("Connect before sending SCAN.")
            return

        if self.scan_active:
            if cmd_stop(self.serial_handler):
                self.scan_active = False
                LOG.info("Sent STOP command to ESP32.")
                self._update_scan_toggle_button()
            else:
                LOG.error("Failed to send STOP command to ESP32.")
        else:
            if cmd_scan(self.serial_handler):
                self.scan_active = True
                LOG.info("Sent SCAN command to ESP32.")
                self._update_scan_toggle_button()
            else:
                LOG.error("Failed to send SCAN command to ESP32.")

    def update_connection_metadata(self):
        metadata = self.serial_handler.device_metadata or {}
        if metadata:
            pieces = [f"{metadata.get('device', 'Unknown')}" ]
            if metadata.get("board"):
                pieces.append(str(metadata["board"]))
            if metadata.get("firmware"):
                pieces.append(str(metadata["firmware"]))
            if metadata.get("protocol") is not None:
                pieces.append(f"Protocol {metadata['protocol']}")
            if metadata.get("sensor"):
                pieces.append(str(metadata["sensor"]))
            text = " · ".join(pieces)
            if metadata.get("serial_number"):
                text += f" (SN: {metadata['serial_number']})"
            self.device_info_label.setText(text)
        else:
            self.device_info_label.setText("No device metadata available")

    def closeEvent(self, event):
        LOG.info(
            "MainWindow.closeEvent | thread_id=%s | thread_name=%s",
            threading.get_ident(),
            threading.current_thread().name,
        )
        try:
            self.serial_worker.stop()
        except Exception as exc:
            LOG.exception("Exception during SerialWorker.stop(): %s", str(exc))
        try:
            self.serial_worker.quit()
        except Exception as exc:
            LOG.exception("Exception during SerialWorker.quit(): %s", str(exc))
        try:
            self.serial_worker.wait(2000)
        except Exception as exc:
            LOG.exception("Exception during SerialWorker.wait(): %s", str(exc))
        try:
            if self.serial_handler.is_connected():
                self.serial_handler.disconnect()
        except Exception as exc:
            LOG.exception("Exception during SerialHandler.disconnect(): %s", str(exc))
        super().closeEvent(event)
