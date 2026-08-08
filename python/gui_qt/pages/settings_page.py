from pathlib import Path

try:
    from serial.tools import list_ports
except Exception:
    list_ports = None

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout, QLabel, QComboBox, QCheckBox,
    QPushButton, QFrame, QMessageBox, QHBoxLayout
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
    def __init__(self, serial_handler, settings=None, on_connection_settings_changed=None, parent=None):
        """
        serial_handler: the shared core.serial_handler.SerialHandler instance.
        settings: optional shared settings dict from MainWindow.
        on_connection_settings_changed: optional callback(port, baud, auto_detect, theme)
            so MainWindow can reconnect / update runtime state when settings change.
        """
        super().__init__(parent)
        self.serial_handler = serial_handler
        self.on_connection_settings_changed = on_connection_settings_changed
        self.settings = settings if settings is not None else load_settings()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(20)

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: #AEB4BD;")
        outer.addWidget(title)

        # ---- connection settings card ----
        conn_card = QFrame()
        conn_card.setObjectName("card")
        conn_form = QFormLayout(conn_card)
        conn_form.setContentsMargins(16, 16, 16, 16)

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

        refresh_btn = QPushButton("Refresh Ports")
        refresh_btn.clicked.connect(self._populate_ports)

        port_controls = QHBoxLayout()
        port_controls.addWidget(self.port_count_label)
        port_controls.addStretch()
        port_controls.addWidget(self.auto_detect_btn)

        conn_form.addRow("ESP32 Device (VID:PID)", self.port_combo)
        conn_form.addRow(port_controls)
        conn_form.addRow("Baud Rate", self.baud_combo)
        conn_form.addRow("", self.auto_reconnect)
        conn_form.addRow("", self.auto_detect_serial)
        outer.addWidget(conn_card)

        # ---- theme card ----
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
        outer.addWidget(theme_card)

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

        fw_layout.addWidget(fw_label)
        fw_layout.addWidget(self.fw_status)
        fw_layout.addWidget(upload_btn)
        fw_layout.addWidget(self.fw_progress)
        outer.addWidget(fw_card)

        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.on_save)
        outer.addWidget(save_btn)

        outer.addStretch()
        self._refresh_firmware_status()
        self._apply_theme(self.settings.get("theme", "dark"))

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
        default_port = get_default_com_port(CONFIG.com_port)
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

        if saved_port and saved_port not in found_devices:
            self.port_combo.insertItem(0, f"{saved_port} (saved)", saved_port)
            found_devices[saved_port] = saved_port
        elif not found_devices and default_port:
            self.port_combo.insertItem(0, default_port, default_port)
            found_devices[default_port] = default_port

        if default_port and default_port not in found_devices:
            self.port_combo.insertItem(0, f"{default_port} (default)", default_port)
            found_devices[default_port] = default_port

        if saved_port and self.port_combo.findData(saved_port) != -1:
            self.port_combo.setCurrentIndex(self.port_combo.findData(saved_port))
        elif default_port and self.port_combo.findData(default_port) != -1:
            self.port_combo.setCurrentIndex(self.port_combo.findData(default_port))

        self.port_count_label.setText(f"Devices found: {self.port_combo.count()}")

    def _refresh_firmware_status(self):
        candidates = discover_firmware_candidates()
        binary = find_firmware_binary()
        status_text = format_firmware_status(binary, candidates)
        self.fw_status.setText(status_text)
        self._upload_btn.setEnabled(binary is not None)

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
        self._upload_btn.setEnabled(True)
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
        self.settings.update({
            "com_port": new_port,
            "baud_rate": new_baud,
            "theme": selected_theme,
            "auto_reconnect": self.auto_reconnect.isChecked(),
            "auto_detect_serial": self.auto_detect_serial.isChecked(),
        })
        self.settings.setdefault("theme", "dark")
        save_settings(self.settings)

        self._apply_theme(selected_theme)

        if self.on_connection_settings_changed:
            self.on_connection_settings_changed(
                new_port,
                new_baud,
                auto_reconnect=self.auto_reconnect.isChecked(),
                auto_detect=self.auto_detect_serial.isChecked(),
                theme=selected_theme,
            )

        QMessageBox.information(self, "Settings", "Settings saved.")
