from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QComboBox, QCheckBox,
    QPushButton, QFrame, QMessageBox
)
import threading

from config import get_config
from settings_store import load_settings, save_settings
from core.firmware_helper import discover_firmware_candidates, find_firmware_binary, upload_firmware_with_progress

CONFIG = get_config()


class SettingsPage(QWidget):
    def __init__(self, serial_handler, on_connection_settings_changed=None, parent=None):
        """
        serial_handler: the shared core.serial_handler.SerialHandler instance.
        on_connection_settings_changed: optional callback(port, baud) so
            MainWindow can reconnect / restart the worker if the user
            changes port or baud while connected.
        """
        super().__init__(parent)
        self.serial_handler = serial_handler
        self.on_connection_settings_changed = on_connection_settings_changed
        self.settings = load_settings()

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
        self._populate_ports()

        self.baud_combo = QComboBox()
        self.baud_combo.addItems([str(b) for b in CONFIG.baud_rates])
        saved_baud = str(self.settings.get("baud_rate", CONFIG.baud_rate))
        if saved_baud in [self.baud_combo.itemText(i) for i in range(self.baud_combo.count())]:
            self.baud_combo.setCurrentText(saved_baud)

        self.auto_reconnect = QCheckBox("Auto-reconnect")
        self.auto_reconnect.setChecked(self.settings.get("auto_reconnect", True))

        refresh_btn = QPushButton("Refresh Ports")
        refresh_btn.clicked.connect(self._populate_ports)

        conn_form.addRow("COM Port", self.port_combo)
        conn_form.addRow("", refresh_btn)
        conn_form.addRow("Baud Rate", self.baud_combo)
        conn_form.addRow("", self.auto_reconnect)
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

    def _populate_ports(self):
        ports = self.serial_handler.list_available_ports() if self.serial_handler else []
        self.port_combo.clear()
        saved_port = self.settings.get("com_port", "") if hasattr(self, "settings") else ""
        items = ports or ([saved_port] if saved_port else [])
        self.port_combo.addItems(items)
        if saved_port and saved_port in items:
            self.port_combo.setCurrentText(saved_port)

    def _refresh_firmware_status(self):
        candidates = discover_firmware_candidates()
        binary = find_firmware_binary()
        if binary is not None:
            self.fw_status.setText(f"Firmware ready: {binary.name}")
            self._upload_btn.setEnabled(True)
        elif candidates:
            self.fw_status.setText(f"Firmware source found (not a .bin): {candidates[0].name}")
            self._upload_btn.setEnabled(False)
        else:
            self.fw_status.setText("No bundled firmware detected.")
            self._upload_btn.setEnabled(False)

    def on_upload_firmware(self):
        port = self.port_combo.currentText().strip()
        if not port:
            QMessageBox.warning(self, "Firmware Upload", "Select a COM port first.")
            return

        self._upload_btn.setEnabled(False)
        self.fw_progress.setText("Starting upload...")

        def progress(line: str):
            self.fw_progress.setText(line)

        def run_upload():
            ok, msg = upload_firmware_with_progress(port=port, progress_callback=progress)
            self._upload_btn.setEnabled(True)
            self.fw_progress.setText(msg)

        threading.Thread(target=run_upload, daemon=True).start()

    def on_save(self):
        new_port = self.port_combo.currentText().strip()
        new_baud = int(self.baud_combo.currentText())

        self.serial_handler.auto_reconnect_enabled = self.auto_reconnect.isChecked()

        self.settings.update({
            "com_port": new_port,
            "baud_rate": new_baud,
            "theme": self.theme_combo.currentText().lower(),
            "auto_reconnect": self.auto_reconnect.isChecked(),
        })
        save_settings(self.settings)

        if self.on_connection_settings_changed:
            self.on_connection_settings_changed(new_port, new_baud)

        QMessageBox.information(self, "Settings", "Settings saved.")
