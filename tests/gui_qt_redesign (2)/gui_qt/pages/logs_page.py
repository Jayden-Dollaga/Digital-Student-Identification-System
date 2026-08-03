from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton


class LogsPage(QWidget):
    """Matches gui/log_page.py's build_log_tab — a live log view with Clear."""

    def __init__(self, parent=None):
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        header_row = QHBoxLayout()
        title = QLabel("Live Log")
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: #AEB4BD;")
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear)
        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addWidget(clear_btn)
        outer.addLayout(header_row)

        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet(
            "background-color: #0F1114; border: 1px solid #262A31; "
            "border-radius: 8px; font-family: 'Consolas', monospace; color: #9AA4B2;"
        )
        self.console.appendPlainText("System ready.")
        outer.addWidget(self.console)

    def append_line(self, line: str):
        """Call this from MainWindow when SerialWorker.log_line fires."""
        self.console.appendPlainText(line)

    def clear(self):
        self.console.clear()
