import logging
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QLabel, QPushButton
)
from PySide6.QtCore import QObject, Signal, QTimer

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
from gui_qt.workers.connection_worker import ConnectionWorker

from core.database import init_database, auto_backup_if_needed
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

        # Automatic backups: back up on startup if the last one is stale,
        # then keep checking periodically while the app runs. The DB is
        # small (a school's worth of students/attendance), so this runs
        # synchronously on the GUI thread rather than needing a dedicated
        # worker - if that ever changes (much larger DB), this should move
        # to a background thread instead. auto_backup_if_needed() never
        # raises, so this can't interrupt startup even if backups are
        # failing for some reason (disk full, permissions, etc.).
        AUTO_BACKUP_INTERVAL_MINUTES = 25
        self._auto_backup_interval_hours = AUTO_BACKUP_INTERVAL_MINUTES / 60.0
        QTimer.singleShot(2000, self._run_auto_backup_check)
        self._auto_backup_timer = QTimer(self)
        self._auto_backup_timer.timeout.connect(self._run_auto_backup_check)
        # Re-check at 1/5th of the actual interval so a backup fires close
        # to its due time instead of drifting - checking is cheap, and a
        # missed check just gets caught on the next one either way.
        self._auto_backup_timer.start(int(AUTO_BACKUP_INTERVAL_MINUTES * 60 * 1000 / 5))

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
        self.connection_worker = ConnectionWorker(self.serial_handler)
        self.students_page = StudentsPage(serial_handler=self.serial_handler, serial_worker=self.serial_worker)
        self.reports_page = ReportsPage()
        self.logs_page = LogsPage(serial_handler=self.serial_handler)
        self.settings_page = SettingsPage(
            serial_handler=self.serial_handler,
            settings=self.settings,
            attendance_processor=self.attendance_processor,
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

        # ---- apply persisted appearance / role settings ----
        self.sidebar.set_compact(bool(self.settings.get("compact_sidebar", False)))
        self._apply_role_permissions(self.settings.get("current_role", CONFIG.default_user_role))

        # ---- connection worker (handles non-blocking serial connect/disconnect) ----
        self.connection_worker.connect_result.connect(self.on_connect_result)
        self.connection_worker.connection_state_changed.connect(self.on_connection_changed)
        self.connection_worker.start()
        LOG.info("Starting ConnectionWorker")

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

        # NOTE: connecting is manual-only by design - the app opens
        # disconnected and waits for you to click "Connect". The
        # "Auto-discover ESP32 on startup" checkbox only controls whether
        # that manual Connect click searches all ports (auto_detect=True)
        # or sticks to the saved port, same as before.

    def _run_auto_backup_check(self):
        path = auto_backup_if_needed(min_interval_hours=self._auto_backup_interval_hours)
        if path:
            LOG.info("Automatic backup created: %s", path)
            if hasattr(self, "reports_page") and hasattr(self.reports_page, "refresh_backup_list"):
                self.reports_page.refresh_backup_list()

    def switch_page(self, key: str):
        self.stack.setCurrentWidget(self._pages[key])
        self.page_title.setText(PAGE_TITLES[key])
        # refresh data-driven pages whenever the user navigates to them
        page = self._pages[key]
        if hasattr(page, "refresh"):
            page.refresh()

    def _apply_role_permissions(self, role_key: str) -> None:
        """Gate destructive/admin pages and actions based on the active role's
        permission list from config.USER_ROLES. Informational only until a real
        login system exists — anyone can still change the role in Settings."""
        role = CONFIG.user_roles.get(role_key, {})
        permissions = set(role.get("permissions", []))

        allowed = {"dashboard", "attendance", "logs", "settings"}
        if "enroll" in permissions or "delete" in permissions or "wipe" in permissions:
            allowed.add("students")
        if "export" in permissions or "backup" in permissions:
            allowed.add("reports")
        self.sidebar.set_enabled_pages(allowed)

        # if the currently-visible page just became restricted, bounce to Dashboard
        current_key = next(
            (k for k, p in self._pages.items() if p is self.stack.currentWidget()), None
        )
        if current_key is not None and current_key not in allowed:
            self.switch_page("dashboard")
            self.sidebar._group.buttons()[self._page_order.index("dashboard")].setChecked(True)

        if hasattr(self.settings_page, "set_admin_mode"):
            self.settings_page.set_admin_mode(bool(role.get("can_manage_users", False)))

    def on_connect_clicked(self):
        """Handle Connect/Disconnect button click using background worker."""
        if self.serial_handler.is_connected():
            # Queue disconnection on background thread
            self.connect_button.setEnabled(False)
            self.connection_worker.disconnect_from_device()
            return

        saved_port = self.settings.get("com_port") or ""
        port = saved_port or get_default_com_port(CONFIG.com_port)
        baud = int(self.settings.get("baud_rate") or 115200)
        
        # Queue connection on background thread (won't block the UI)
        self.connect_button.setEnabled(False)
        self.connection_worker.connect_to_device(port, baud, auto_detect=self.auto_detect_serial)

    def on_connect_result(self, success: bool, message: str):
        """Handle connection result from ConnectionWorker."""
        try:
            self.connect_button.setEnabled(True)
            
            if success:
                saved_port = self.settings.get("com_port") or ""
                port = saved_port or get_default_com_port(CONFIG.com_port)
                baud = int(self.settings.get("baud_rate") or 115200)
                
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
                # The app deliberately avoids resetting the ESP32 on connect
                # (a DTR/RTS reset would drop active scan mode), unlike the
                # Arduino IDE Serial Monitor, which always resets on open and
                # so always shows a fresh boot banner. That means if the
                # device was already sitting idle, the monitor can look
                # "frozen" here even though it's working correctly - nothing
                # new prints until you send a command. Say so explicitly so
                # it doesn't look broken.
                self.logs_page.append_line(
                    "--- Connected. If no boot banner appeared above, the device was "
                    "already running (connecting here never resets it, to protect an "
                    "active scan). Send a command below, or use 'Reset Device' to see "
                    "the full boot banner. ---"
                )
            else:
                LOG.error("Connection failed: %s", message)
                self.connect_button.setText("Connect")
                self.update_connection_metadata()
                self.logs_page.set_connection_state("disconnected")
        except Exception as exc:
            LOG.exception("Exception in on_connect_result", error=str(exc))
            self.connect_button.setEnabled(True)
            self.connect_button.setText("Connect")
            try:
                self.update_connection_metadata()
            except Exception:
                pass

    def on_connection_settings_changed(
        self,
        port: str,
        baud: int,
        auto_reconnect: Optional[bool] = None,
        auto_detect: Optional[bool] = None,
        theme: Optional[str] = None,
        compact_sidebar: Optional[bool] = None,
        current_role: Optional[str] = None,
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
        if compact_sidebar is not None:
            self.settings["compact_sidebar"] = bool(compact_sidebar)
            self.sidebar.set_compact(bool(compact_sidebar))
        if current_role is not None:
            self.settings["current_role"] = current_role
            self._apply_role_permissions(current_role)

        if self.serial_handler.is_connected():
            self.serial_handler.disconnect()
            ok, msg = self.serial_handler.connect(port, baud)
            if not ok:
                LOG.error("Reconnect failed: %s", msg)

    class _LogBridge(QObject):
        """Carries log records from whatever thread logged them onto the GUI
        thread via a proper Qt signal.

        _QtLogHandler.emit() used to call self.log_page.append_record(record)
        directly - a plain Python method call from whatever thread the log
        line originated on (ConnectionWorker, SerialWorker, a reconnect
        thread, etc.), touching a QPlainTextEdit outside the GUI thread.
        That's undefined behavior in Qt: it can appear to work most of the
        time (posted paint events often still get picked up), but it isn't
        guaranteed to, and appeared to be part of why the Application Log
        sometimes updated live while other GUI state didn't. raw_line
        already did this correctly via Signal/Slot; this makes the log
        bridge do the same instead of being the odd one out.
        """
        record_ready = Signal(object)

    class _QtLogHandler(logging.Handler):
        def __init__(self, log_page):
            super().__init__()
            self.log_page = log_page
            self.setFormatter(AppFormatter("%(asctime)s | %(levelname)-7s | %(source)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S.%f"))
            self._bridge = MainWindow._LogBridge()
            self._bridge.record_ready.connect(self.log_page.append_record)

        def emit(self, record):
            try:
                self._bridge.record_ready.emit(record)
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

    def _set_scan_block_reason(self, reason: Optional[str]):
        self._scan_block_reason = reason

    def _clear_scan_block_reason(self):
        self._scan_block_reason = None

    def _scan_command_blocked_reason(self) -> Optional[str]:
        scan_active = getattr(self, "scan_active", False)
        if scan_active:
            return None

        if getattr(self, "_scan_block_reason", None):
            return self._scan_block_reason
        if getattr(self, "_scan_blocked", False):
            return "A fingerprint enrollment is currently active. Finish or cancel it before scanning."

        serial_handler = getattr(self, "serial_handler", None)
        if serial_handler is None:
            return "Connect to the ESP32 before starting scan mode."
        if not getattr(serial_handler, "is_connected", lambda: False)():
            return "Connect to the ESP32 before starting scan mode."
        return None

    def _can_start_scan(self) -> bool:
        return self._scan_command_blocked_reason() is None

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
            return

        reason = self._scan_command_blocked_reason()
        if reason is not None:
            LOG.warning(reason)
            return

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

        # Keep the Settings page's "Connected Device" panel in sync with the
        # top bar - it mirrors this same info in full detail, live, instead
        # of the old static "COM8 (saved)" field that never reflected what
        # was actually connected.
        if hasattr(self, "settings_page") and hasattr(self.settings_page, "refresh_connection_status"):
            self.settings_page.refresh_connection_status()

    def closeEvent(self, event):
        LOG.info(
            "MainWindow.closeEvent | thread_id=%s | thread_name=%s",
            threading.get_ident(),
            threading.current_thread().name,
        )
        # Stop ConnectionWorker before SerialWorker
        try:
            try:
                self.connection_worker.connect_result.disconnect(self.on_connect_result)
            except Exception:
                pass
            try:
                self.connection_worker.connection_state_changed.disconnect(self.on_connection_changed)
            except Exception:
                pass
            self.connection_worker.stop()
        except Exception as exc:
            LOG.exception("Exception during ConnectionWorker shutdown: %s", str(exc))

        # Disconnect SerialWorker signals from UI slots before shutdown to
        # avoid delivering signals to widgets that are being destroyed.
        try:
            try:
                self.serial_worker.connection_changed.disconnect(self.on_connection_changed)
            except Exception:
                pass
            try:
                self.serial_worker.mode_changed.disconnect(self.on_scan_mode_changed)
            except Exception:
                pass
            try:
                self.serial_worker.scan_event.disconnect(self.on_scan_event)
            except Exception:
                pass
            try:
                self.serial_worker.raw_line.disconnect(self.logs_page.append_line)
            except Exception:
                pass
            try:
                self.serial_worker.error.disconnect(self.on_serial_error)
            except Exception:
                pass

            self.serial_worker.stop()
        except Exception as exc:
            LOG.exception("Exception during SerialWorker shutdown: %s", str(exc))
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

        # Detach the per-window Qt log handler from the shared, process-wide
        # LOG logger. Without this, every MainWindow instantiation leaks a
        # handler that holds a reference to this window's (now-destroyed)
        # logs_page. Any subsequent LOG call — including ones from other
        # still-running windows or background threads — walks *all*
        # registered handlers and invokes emit() on the stale ones too,
        # touching a deleted Qt/C++ widget. That's a plausible root cause of
        # the intermittent native shutdown crash described in
        # docs/Development/SHUTDOWN_CRASH.md.
        try:
            LOG.removeHandler(self._log_handler)
        except Exception as exc:
            LOG.exception("Exception removing Qt log handler: %s", str(exc))

        super().closeEvent(event)