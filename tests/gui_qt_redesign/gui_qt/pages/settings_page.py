from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QComboBox, QCheckBox,
    QPushButton, QFrame, QProgressBar
)

# TODO: from core import settings_store, firmware_helper


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

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
        self.port_combo.addItems(["Auto-detect", "COM3", "COM4", "COM5"])  # TODO: populate from serial_handler
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "115200"])
        self.auto_reconnect = QCheckBox("Auto-reconnect")
        self.auto_reconnect.setChecked(True)

        conn_form.addRow("COM Port", self.port_combo)
        conn_form.addRow("Baud Rate", self.baud_combo)
        conn_form.addRow("", self.auto_reconnect)
        outer.addWidget(conn_card)

        # ---- firmware card ----
        fw_card = QFrame()
        fw_card.setObjectName("card")
        fw_layout = QVBoxLayout(fw_card)
        fw_layout.setContentsMargins(16, 16, 16, 16)

        fw_label = QLabel("Firmware")
        fw_label.setObjectName("cardLabel")
        self.fw_status = QLabel("No firmware detected")
        self.fw_status.setStyleSheet("color: #8A909C;")
        self.fw_progress = QProgressBar()
        self.fw_progress.setValue(0)
        upload_btn = QPushButton("Upload Firmware")
        upload_btn.setObjectName("primaryButton")
        upload_btn.clicked.connect(self.on_upload_firmware)

        fw_layout.addWidget(fw_label)
        fw_layout.addWidget(self.fw_status)
        fw_layout.addWidget(self.fw_progress)
        fw_layout.addWidget(upload_btn)
        outer.addWidget(fw_card)

        outer.addStretch()

    def on_upload_firmware(self):
        # TODO: firmware_helper.upload(port=..., progress_callback=self.fw_progress.setValue)
        pass
