import re
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QLineEdit,
    QCheckBox,
    QSplitter,
)

from core.utils import parse_json_line


class LogsPage(QWidget):
    """A two-panel log and serial monitor interface."""

    _formatted_re = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3,6} \| .+")
    _bracket_level_re = re.compile(r"^\s*\[([^\]]+)\]\s*(.*)$")

    def __init__(self, serial_handler=None, parent=None):
        super().__init__(parent)
        self.serial_handler = serial_handler
        self._paused = False
        self._auto_scroll = True
        self._pending_serial_lines = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        splitter = QSplitter(Qt.Vertical, self)
        splitter.setHandleWidth(8)

        # Application log panel
        app_panel = QWidget()
        app_layout = QVBoxLayout(app_panel)
        app_layout.setContentsMargins(0, 0, 0, 0)
        app_layout.setSpacing(12)

        app_header_row = QHBoxLayout()
        app_title = QLabel("Application Log")
        app_title.setStyleSheet("font-size: 15px; font-weight: 600; color: #AEB4BD;")
        app_clear_btn = QPushButton("Clear")
        app_clear_btn.clicked.connect(self.clear_app_log)
        app_header_row.addWidget(app_title)
        app_header_row.addStretch()
        app_header_row.addWidget(app_clear_btn)
        app_layout.addLayout(app_header_row)

        self.app_console = QPlainTextEdit()
        self.app_console.setReadOnly(True)
        self.app_console.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.app_console.setCenterOnScroll(False)
        self.app_console.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self.app_console.setStyleSheet(
            "background-color: #0F1114; border: 1px solid #262A31; "
            "border-radius: 8px; font-family: 'Consolas', monospace; font-size: 12px; color: #9AA4B2;"
        )
        self.app_console.appendPlainText("System ready.")
        app_layout.addWidget(self.app_console)

        splitter.addWidget(app_panel)

        # Serial monitor panel
        monitor_panel = QWidget()
        monitor_layout = QVBoxLayout(monitor_panel)
        monitor_layout.setContentsMargins(0, 0, 0, 0)
        monitor_layout.setSpacing(12)

        monitor_header_row = QHBoxLayout()
        monitor_title = QLabel("Serial Monitor")
        monitor_title.setStyleSheet("font-size: 15px; font-weight: 600; color: #AEB4BD;")
        monitor_header_row.addWidget(monitor_title)
        monitor_header_row.addStretch()
        monitor_layout.addLayout(monitor_header_row)

        status_row = QHBoxLayout()
        self.port_label = QLabel("Port: N/A")
        self.baud_label = QLabel("Baud: N/A")
        self.connection_label = QLabel("State: Disconnected")
        for label in (self.port_label, self.baud_label, self.connection_label):
            label.setStyleSheet("font-size: 11px; color: #AEB4BD;")
        status_row.addWidget(self.port_label)
        status_row.addSpacing(16)
        status_row.addWidget(self.baud_label)
        status_row.addSpacing(16)
        status_row.addWidget(self.connection_label)
        status_row.addStretch()
        monitor_layout.addLayout(status_row)

        self.monitor_console = QPlainTextEdit()
        self.monitor_console.setReadOnly(True)
        self.monitor_console.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.monitor_console.setCenterOnScroll(False)
        self.monitor_console.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self.monitor_console.setStyleSheet(
            "background-color: #050607; border: 1px solid #1E2228; "
            "border-radius: 8px; font-family: 'Consolas', monospace; font-size: 12px; color: #E6E8EB;"
        )
        monitor_layout.addWidget(self.monitor_console)

        controls_row = QHBoxLayout()
        self.clear_monitor_btn = QPushButton("Clear")
        self.clear_monitor_btn.clicked.connect(self.clear_monitor)
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.pause_monitor)
        self.resume_btn = QPushButton("Resume")
        self.resume_btn.clicked.connect(self.resume_monitor)
        self.resume_btn.setEnabled(False)
        self.auto_scroll_checkbox = QCheckBox("Auto-scroll")
        self.auto_scroll_checkbox.setChecked(True)
        self.auto_scroll_checkbox.stateChanged.connect(self._set_auto_scroll)
        controls_row.addWidget(self.clear_monitor_btn)
        controls_row.addWidget(self.pause_btn)
        controls_row.addWidget(self.resume_btn)
        controls_row.addSpacing(12)
        controls_row.addWidget(self.auto_scroll_checkbox)
        controls_row.addStretch()
        monitor_layout.addLayout(controls_row)

        send_row = QHBoxLayout()
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter command and press Send")
        self.command_input.returnPressed.connect(self.send_command)
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_command)
        send_row.addWidget(self.command_input)
        send_row.addWidget(self.send_btn)
        monitor_layout.addLayout(send_row)

        splitter.addWidget(monitor_panel)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 6)
        outer.addWidget(splitter)

    @property
    def console(self):
        return self.app_console

    @property
    def monitor(self):
        return self.monitor_console

    def clear(self):
        self.clear_app_log()
        self.clear_monitor()

    def append_line(self, line: str):
        self.append_serial_line(line)

    def append_serial_line(self, line: str):
        if line is None:
            return

        text = str(line)
        if self._paused:
            self._pending_serial_lines.append(text)
            return

        self._append_serial_text(text)

    def append_record(self, record):
        if record is None:
            return
        try:
            formatted = record.getMessage()
        except Exception:
            formatted = str(record)

        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        level = record.levelname
        source = getattr(record, "source", "SYSTEM")
        line = f"{timestamp} | {level:<7} | {source:<8} | {formatted}"
        self._append_app_text(line)

    def set_connection_state(self, state: str):
        labels = {
            "connected": "State: Connected",
            "disconnected": "State: Disconnected",
            "connecting": "State: Connecting…",
        }
        self.connection_label.setText(labels.get(state, f"State: {state}"))

    def set_connection_info(self, port: str, baud: int):
        self.port_label.setText(f"Port: {port or 'N/A'}")
        self.baud_label.setText(f"Baud: {baud or 'N/A'}")

    def clear_app_log(self):
        self.app_console.clear()
        self.app_console.appendPlainText("System ready.")

    def clear_monitor(self):
        self.monitor_console.clear()
        self._pending_serial_lines.clear()

    def pause_monitor(self):
        self._paused = True
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(True)

    def resume_monitor(self):
        self._paused = False
        self.resume_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        while self._pending_serial_lines:
            self._append_serial_text(self._pending_serial_lines.pop(0))

    def _set_auto_scroll(self, state: int):
        self._auto_scroll = bool(state)

    def send_command(self):
        if self.serial_handler is None:
            return
        command = self.command_input.text().strip()
        if not command:
            return
        self.serial_handler.send_command(command)
        self.command_input.clear()

    def _append_app_text(self, text: str):
        scrollbar = self.app_console.verticalScrollBar()
        auto_scroll = scrollbar.value() == scrollbar.maximum()
        self.app_console.appendPlainText(text)
        if auto_scroll:
            scrollbar.setValue(scrollbar.maximum())

    def _append_serial_text(self, text: str):
        scrollbar = self.monitor_console.verticalScrollBar()
        auto_scroll = scrollbar.value() == scrollbar.maximum()
        self.monitor_console.appendPlainText(text)
        if self._auto_scroll and auto_scroll:
            scrollbar.setValue(scrollbar.maximum())
