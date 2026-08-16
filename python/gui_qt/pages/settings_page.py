import os
import subprocess
import sys
from pathlib import Path

try:
    from serial.tools import list_ports
except Exception:
    list_ports = None

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout, QLabel, QComboBox, QCheckBox,
    QPushButton, QFrame, QMessageBox, QHBoxLayout, QSpinBox, QScrollArea
)
from PySide6.QtCore import QThread, Signal

from config import get_config, get_default_com_port
from settings_store import load_settings, save_settings
from core.firmware_helper import discover_firmware_candidates, find_firmware_binary, upload_firmware_with_progress

CONFIG = get_config()


def format_firmware_status(binary_path=None, candidates=None):
    if binary_path is not None:
        return f"Firmware ready: {binary_path.name}"
    if candidates:
        return f"Firmware source found (not a .bin): {candidates[0].name}"
    return "No bundled firmware detected."


class FirmwareUploadWorker(QThread):
    progress = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, port: str, parent=None):
        super().__init__(parent)
        self.port = port

    def run(self):
        ok, msg = upload_firmware_with_progress(port=self.port, progress_callback=self.progress.emit)
        self.finished.emit(ok, msg)


class SettingsPage(QWidget):
    def __init__(
        self,
        serial_handler,
        settings=None,
        attendance_processor=None,
        on_connection_settings_changed=None,
        parent=None,
    ):
        """
        serial_handler: the shared core.serial_handler.SerialHandler instance.
        settings: optional shared settings dict from MainWindow.
        attendance_processor: the shared core.attendance.AttendanceProcessor instance,
            so cooldown/min-confidence changes take effect immediately.
        on_connection_settings_changed: optional callback(port, baud, auto_reconnect,
            auto_detect, theme, compact_sidebar, current_role) so MainWindow can
            reconnect / update runtime state when settings change.
        """
        super().__init__(parent)
        self.serial_handler = serial_handler
        self.attendance_processor = attendance_processor
        self.on_connection_settings_changed = on_connection_settings_changed
        self.settings = settings if settings is not None else load_settings()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        outer = QVBoxLayout(content)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(20)

        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(content)
        page_layout.addWidget(scroll)

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: #AEB4BD;")
        outer.addWidget(title)

        # ---- connection card (device info + manual override, merged into one box) ----
        # This replaces the old "ESP32 Device (VID:PID)" field that just
        # showed whatever port was last saved (e.g. "COM8 (saved)") even
        # when nothing was actually connected, or a different device was.
        # Combined into a single card per the layout: one big detail block
        # up top, then the override controls as compact rows below it,
        # instead of two separate boxes with a gap between them.
        conn_card = QFrame()
        conn_card.setObjectName("card")
        conn_layout = QVBoxLayout(conn_card)
        conn_layout.setContentsMargins(16, 16, 16, 16)
        conn_layout.setSpacing(10)

        device_header = QHBoxLayout()
        device_title = QLabel("Connected Device")
        device_title.setObjectName("cardLabel")
        self.device_status_label = QLabel("● Disconnected")
        self.device_status_label.setStyleSheet("color: #E5484D; font-weight: 600;")
        device_header.addWidget(device_title)
        device_header.addStretch()
        device_header.addWidget(self.device_status_label)
        conn_layout.addLayout(device_header)

        self.device_detail_label = QLabel("No device connected yet.")
        self.device_detail_label.setWordWrap(True)
        self.device_detail_label.setStyleSheet("color: #AEB4BD; font-size: 12px;")
        conn_layout.addWidget(self.device_detail_label)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #2A2E36; background-color: #2A2E36;")
        divider.setFixedHeight(1)
        conn_layout.addWidget(divider)

        override_title = QLabel("Manual Port Override (optional)")
        override_title.setStyleSheet("color: #8A909C; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        conn_layout.addWidget(override_title)

        override_form = QFormLayout()

        self.port_combo = QComboBox()
        self.port_combo.setEditable(True)
        self.port_combo.setMinimumWidth(320)

        self.port_count_label = QLabel("")
        self.port_count_label.setStyleSheet("color: #AEB4BD;")

        self._populate_ports()

        self.auto_detect_btn = QPushButton("Refresh device list")
        self.auto_detect_btn.setObjectName("secondaryButton")
        self.auto_detect_btn.clicked.connect(self._populate_ports)

        self.baud_combo = QComboBox()
        self.baud_combo.addItems([str(b) for b in CONFIG.baud_rates])
        saved_baud = str(self.settings.get("baud_rate", CONFIG.baud_rate))
        if saved_baud in [self.baud_combo.itemText(i) for i in range(self.baud_combo.count())]:
            self.baud_combo.setCurrentText(saved_baud)

        self.auto_reconnect = QCheckBox("Auto-reconnect")
        self.auto_reconnect.setChecked(self.settings.get("auto_reconnect", True))

        self.auto_detect_serial = QCheckBox("Auto-discover ESP32 on startup")
        self.auto_detect_serial.setChecked(self.settings.get("auto_detect_serial", True))

        port_controls = QHBoxLayout()
        port_controls.addWidget(self.port_count_label)
        port_controls.addStretch()
        port_controls.addWidget(self.auto_detect_btn)

        override_hint = QLabel(
            "Only needed if auto-discovery can't find your device, or to pick a specific "
            "port for firmware upload. Otherwise leave this alone — the app finds the ESP32 "
            "on its own and the panel above will show it once connected."
        )
        override_hint.setWordWrap(True)
        override_hint.setStyleSheet("color: #8A909C; font-size: 11px;")

        override_form.addRow("Port override", self.port_combo)
        override_form.addRow(port_controls)
        override_form.addRow("Baud Rate", self.baud_combo)
        override_form.addRow("", self.auto_reconnect)
        override_form.addRow("", self.auto_detect_serial)
        override_form.addRow("", override_hint)
        conn_layout.addLayout(override_form)

        outer.addWidget(self._section_label("Connection"))
        outer.addWidget(conn_card)

        # ---- attendance behavior card ----
        attendance_card = QFrame()
        attendance_card.setObjectName("card")
        attendance_form = QFormLayout(attendance_card)
        attendance_form.setContentsMargins(16, 16, 16, 16)

        self.cooldown_spin = QSpinBox()
        self.cooldown_spin.setRange(0, 600)
        self.cooldown_spin.setSuffix(" s")
        self.cooldown_spin.setValue(int(self.settings.get("cooldown", CONFIG.cooldown_seconds)))

        self.min_confidence_spin = QSpinBox()
        self.min_confidence_spin.setRange(0, 255)
        self.min_confidence_spin.setValue(int(self.settings.get("min_confidence", CONFIG.min_confidence)))

        attendance_form.addRow("Scan cooldown", self.cooldown_spin)
        attendance_form.addRow("Minimum match confidence", self.min_confidence_spin)
        hint = QLabel("Lower confidence accepts weaker fingerprint matches; cooldown blocks repeat scans of the same student.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #8A909C; font-size: 11px;")
        attendance_form.addRow("", hint)

        outer.addWidget(self._section_label("Attendance Behavior"))
        outer.addWidget(attendance_card)

        # ---- appearance card ----
        theme_card = QFrame()
        theme_card.setObjectName("card")
        theme_form = QFormLayout(theme_card)
        theme_form.setContentsMargins(16, 16, 16, 16)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(CONFIG.theme_modes))
        saved_theme = self.settings.get("theme", "dark")
        match = [t for t in CONFIG.theme_modes if t.lower() == saved_theme.lower()]
        if match:
            self.theme_combo.setCurrentText(match[0])
        theme_form.addRow("Theme Mode", self.theme_combo)

        self.compact_sidebar_check = QCheckBox("Compact sidebar (icons only)")
        self.compact_sidebar_check.setChecked(bool(self.settings.get("compact_sidebar", False)))
        theme_form.addRow("", self.compact_sidebar_check)

        outer.addWidget(self._section_label("Appearance"))
        outer.addWidget(theme_card)

        # ---- role card ----
        role_card = QFrame()
        role_card.setObjectName("card")
        role_form = QFormLayout(role_card)
        role_form.setContentsMargins(16, 16, 16, 16)

        self.role_combo = QComboBox()
        self._role_keys = list(CONFIG.user_roles.keys())
        for key in self._role_keys:
            self.role_combo.addItem(CONFIG.user_roles[key].get("name", key), key)
        saved_role = self.settings.get("current_role", CONFIG.default_user_role)
        if saved_role in self._role_keys:
            self.role_combo.setCurrentIndex(self._role_keys.index(saved_role))
        self.role_combo.currentIndexChanged.connect(self._update_permissions_label)

        self.permissions_label = QLabel("")
        self.permissions_label.setWordWrap(True)
        self.permissions_label.setStyleSheet("color: #8A909C; font-size: 11px;")

        role_form.addRow("Active role", self.role_combo)
        role_form.addRow("Permissions", self.permissions_label)
        note = QLabel("No login is enforced yet — this only hides admin-only pages/actions in the UI.")
        note.setWordWrap(True)
        note.setStyleSheet("color: #8A909C; font-size: 11px;")
        role_form.addRow("", note)
        self._update_permissions_label()

        outer.addWidget(self._section_label("User Role"))
        outer.addWidget(role_card)

        # ---- logging & diagnostics card ----
        log_card = QFrame()
        log_card.setObjectName("card")
        log_form = QFormLayout(log_card)
        log_form.setContentsMargins(16, 16, 16, 16)

        self.log_to_file_check = QCheckBox("Write logs to file")
        self.log_to_file_check.setChecked(bool(self.settings.get("log_to_file", CONFIG.log_to_file)))

        self.debug_logging_check = QCheckBox("Verbose debug logging")
        self.debug_logging_check.setChecked(bool(self.settings.get("enable_debug_logging", CONFIG.enable_debug_logging)))

        log_form.addRow("", self.log_to_file_check)
        log_form.addRow("", self.debug_logging_check)

        restart_note = QLabel("Logging changes take effect the next time the app starts.")
        restart_note.setWordWrap(True)
        restart_note.setStyleSheet("color: #8A909C; font-size: 11px;")
        log_form.addRow("", restart_note)

        log_folder = str(Path(CONFIG.log_folder).resolve())
        log_path_row = QHBoxLayout()
        log_path_label = QLabel(log_folder)
        log_path_label.setStyleSheet("color: #AEB4BD;")
        open_log_btn = QPushButton("Open Log Folder")
        open_log_btn.setObjectName("secondaryButton")
        open_log_btn.clicked.connect(lambda: self._open_folder(log_folder))
        log_path_row.addWidget(log_path_label)
        log_path_row.addStretch()
        log_path_row.addWidget(open_log_btn)
        log_form.addRow("Log folder", log_path_row)

        outer.addWidget(self._section_label("Logging & Diagnostics"))
        outer.addWidget(log_card)

        # ---- firmware card ----
        fw_card = QFrame()
        fw_card.setObjectName("card")
        fw_layout = QVBoxLayout(fw_card)
        fw_layout.setContentsMargins(16, 16, 16, 16)

        fw_label = QLabel("Firmware")
        fw_label.setObjectName("cardLabel")
        self.fw_status = QLabel("")
        self.fw_status.setStyleSheet("color: #8A909C;")
        self.fw_status.setWordWrap(True)
        self.fw_progress = QLabel("")
        self.fw_progress.setWordWrap(True)
        upload_btn = QPushButton("Upload Firmware")
        upload_btn.setObjectName("primaryButton")
        upload_btn.clicked.connect(self.on_upload_firmware)
        self._upload_btn = upload_btn
        self._upload_worker = None
        self._upload_in_progress = False
        self._fw_binary_available = False

        fw_layout.addWidget(fw_label)
        fw_layout.addWidget(self.fw_status)
        fw_layout.addWidget(upload_btn)
        fw_layout.addWidget(self.fw_progress)
        outer.addWidget(self._section_label("Firmware"))
        outer.addWidget(fw_card)

        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.on_save)
        outer.addWidget(save_btn)

        outer.addStretch()
        self._refresh_firmware_status()
        self._apply_theme(self.settings.get("theme", "dark"))
        self.set_admin_mode(CONFIG.user_roles.get(saved_role, {}).get("can_manage_users", False))
        self.refresh_connection_status()

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("color: #8A909C; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        return label

    def refresh(self):
        """Called automatically by MainWindow.switch_page() every time the
        user navigates to Settings, so the port list and connection panel
        are rescanned live instead of only reflecting whatever was true
        when the app first started (or the last time this page happened
        to be rebuilt)."""
        self._populate_ports()
        self.refresh_connection_status()

    def refresh_connection_status(self):
        """Update the live 'Connected Device' panel from the shared SerialHandler.

        Called on init and again by MainWindow.update_connection_metadata()
        every time the connection state or device metadata changes, so this
        panel always reflects what's actually plugged in - full detail,
        same source of truth as the top bar - instead of a static saved
        port string that could easily be stale or wrong.
        """
        handler = self.serial_handler
        is_connected = bool(handler and handler.is_connected())

        if is_connected:
            self.device_status_label.setText("● Connected")
            self.device_status_label.setStyleSheet("color: #3FB950; font-weight: 600;")
        else:
            self.device_status_label.setText("● Disconnected")
            self.device_status_label.setStyleSheet("color: #E5484D; font-weight: 600;")

        metadata = (getattr(handler, "device_metadata", None) or {}) if handler else {}
        port = getattr(handler, "reconnect_port", None) if handler else None
        baud = getattr(handler, "reconnect_baud", None) if handler else None

        if not is_connected or not metadata:
            self.device_detail_label.setText(
                "No device connected yet. Connect from the top bar - this panel "
                "will fill in automatically once a device responds."
            )
            return

        lines = []
        if port:
            lines.append(f"Port: {port}")
        if baud:
            lines.append(f"Baud: {baud}")
        if metadata.get("device"):
            lines.append(f"Device: {metadata['device']}")
        if metadata.get("board"):
            lines.append(f"Board: {metadata['board']}")
        if metadata.get("firmware"):
            lines.append(f"Firmware: {metadata['firmware']}")
        if metadata.get("protocol") is not None:
            lines.append(f"Protocol: {metadata['protocol']}")
        if metadata.get("sensor"):
            lines.append(f"Sensor: {metadata['sensor']}")
        if metadata.get("serial_number"):
            lines.append(f"Serial Number: {metadata['serial_number']}")

        self.device_detail_label.setText(
            "\n".join(lines) if lines else "Connected, but the device hasn't reported its metadata yet."
        )

    def _update_permissions_label(self):
        key = self.role_combo.currentData()
        role = CONFIG.user_roles.get(key, {})
        perms = role.get("permissions", [])
        self.permissions_label.setText(", ".join(perms) if perms else "None")

    def set_admin_mode(self, is_admin: bool) -> None:
        """Gate the firmware upload button behind the admin role (destructive action)."""
        is_admin = bool(is_admin)
        self._upload_btn.setEnabled(is_admin and self._fw_binary_available)
        if not is_admin:
            self._upload_btn.setToolTip("Only the Administrator role can flash firmware.")
        else:
            self._upload_btn.setToolTip("")

    def _open_folder(self, path: str) -> None:
        try:
            os.makedirs(path, exist_ok=True)
            if sys.platform.startswith("win"):
                os.startfile(path)  # noqa: S606 - Windows-only helper
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as exc:
            QMessageBox.warning(self, "Open Log Folder", f"Could not open folder: {exc}")

    def _get_theme_path(self, theme: str) -> Path:
        theme_file = "theme_light.qss" if theme.lower() == "light" else "theme.qss"
        return Path(__file__).resolve().parents[1] / theme_file

    def _apply_theme(self, theme: str) -> None:
        app = QApplication.instance()
        if app is None:
            return
        qss_file = self._get_theme_path(theme)
        if qss_file.exists():
            app.setStyleSheet(qss_file.read_text(encoding="utf-8", errors="replace"))
        else:
            app.setStyleSheet("")

    def _populate_ports(self):
        self.port_combo.clear()
        saved_port = self.settings.get("com_port", "") if hasattr(self, "settings") else ""
        found_devices = {}

        if self.serial_handler:
            if list_ports is not None:
                try:
                    for port_info in list_ports.comports():
                        device = getattr(port_info, "device", None)
                        if not device:
                            continue
                        vid = getattr(port_info, "vid", None)
                        pid = getattr(port_info, "pid", None)
                        vid_pid = "UNKNOWN"
                        if vid is not None and pid is not None:
                            vid_pid = f"{vid:04x}:{pid:04x}"
                        description = (getattr(port_info, "description", "") or "").strip()
                        label = f"{vid_pid} — {device}"
                        if description:
                            label += f" ({description})"
                        self.port_combo.addItem(label, device)
                        found_devices[device] = label
                except Exception:
                    pass
            else:
                for device in self.serial_handler.list_available_ports():
                    self.port_combo.addItem(device, device)
                    found_devices[device] = device

        # Previously, a saved port that wasn't actually plugged in anymore
        # still got inserted as "<port> (saved)" and pre-selected - so on a
        # fresh launch (or after unplugging the device) this field looked
        # like it had already found something, when really it was just
        # replaying a stale value. Now: only pre-select the saved port if
        # it's genuinely present in this live scan. Otherwise leave the
        # field on its placeholder, same idea as the "Connected Device"
        # panel saying "No device connected yet" instead of guessing.
        if saved_port and self.port_combo.findData(saved_port) != -1:
            self.port_combo.setCurrentIndex(self.port_combo.findData(saved_port))
        else:
            self.port_combo.setCurrentIndex(-1)
            line_edit = self.port_combo.lineEdit()
            if line_edit is not None:
                line_edit.clear()

        line_edit = self.port_combo.lineEdit()
        if line_edit is not None:
            line_edit.setPlaceholderText(
                "Select a detected port…" if found_devices else "No device metadata — click Refresh"
            )

        self.port_count_label.setText(f"Devices found: {len(found_devices)}")

    def _refresh_firmware_status(self):
        candidates = discover_firmware_candidates()
        binary = find_firmware_binary()
        status_text = format_firmware_status(binary, candidates)
        self.fw_status.setText(status_text)
        self._fw_binary_available = binary is not None
        is_admin = CONFIG.user_roles.get(self.role_combo.currentData(), {}).get("can_manage_users", False)
        self._upload_btn.setEnabled(self._fw_binary_available and is_admin)

    def on_upload_firmware(self):
        if self._upload_in_progress:
            QMessageBox.information(self, "Firmware Upload", "An upload is already in progress.")
            return

        port = self.port_combo.currentData() or self.port_combo.currentText().strip()
        if not port:
            QMessageBox.warning(self, "Firmware Upload", "Select a device first.")
            return

        self._upload_in_progress = True
        self._upload_btn.setEnabled(False)
        self.fw_progress.setText("Starting upload...")

        self._upload_worker = FirmwareUploadWorker(port, self)
        self._upload_worker.progress.connect(self._update_upload_progress)
        self._upload_worker.finished.connect(self._finish_upload)
        self._upload_worker.start()

    def _update_upload_progress(self, line: str):
        self.fw_progress.setText(line)

    def _finish_upload(self, ok: bool, msg: str):
        self._upload_in_progress = False
        is_admin = CONFIG.user_roles.get(self.role_combo.currentData(), {}).get("can_manage_users", False)
        self._upload_btn.setEnabled(self._fw_binary_available and is_admin)
        self.fw_progress.setText(msg)
        if ok:
            self.fw_status.setText("Firmware upload completed successfully.")
        else:
            self.fw_status.setText("Firmware upload failed. Check the log output above.")

    def on_save(self):
        new_port = self.port_combo.currentData() or self.port_combo.currentText().strip()
        if not new_port:
            new_port = get_default_com_port(CONFIG.com_port)

        new_baud = int(self.baud_combo.currentText())
        self.serial_handler.auto_reconnect_enabled = self.auto_reconnect.isChecked()

        selected_theme = self.theme_combo.currentText().lower()
        selected_role = self.role_combo.currentData()
        cooldown = self.cooldown_spin.value()
        min_confidence = self.min_confidence_spin.value()
        compact_sidebar = self.compact_sidebar_check.isChecked()

        self.settings.update({
            "com_port": new_port,
            "baud_rate": new_baud,
            "theme": selected_theme,
            "auto_reconnect": self.auto_reconnect.isChecked(),
            "auto_detect_serial": self.auto_detect_serial.isChecked(),
            "cooldown": cooldown,
            "min_confidence": min_confidence,
            "compact_sidebar": compact_sidebar,
            "current_role": selected_role,
            "log_to_file": self.log_to_file_check.isChecked(),
            "enable_debug_logging": self.debug_logging_check.isChecked(),
        })
        self.settings.setdefault("theme", "dark")
        save_settings(self.settings)

        self._apply_theme(selected_theme)
        self.set_admin_mode(CONFIG.user_roles.get(selected_role, {}).get("can_manage_users", False))
        self._refresh_firmware_status()

        if self.attendance_processor is not None:
            self.attendance_processor.cooldown_seconds = cooldown
            self.attendance_processor.min_confidence = min_confidence

        if self.on_connection_settings_changed:
            self.on_connection_settings_changed(
                new_port,
                new_baud,
                auto_reconnect=self.auto_reconnect.isChecked(),
                auto_detect=self.auto_detect_serial.isChecked(),
                theme=selected_theme,
                compact_sidebar=compact_sidebar,
                current_role=selected_role,
            )

        QMessageBox.information(self, "Settings", "Settings saved.")