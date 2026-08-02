from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPlainTextEdit


class LogsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        title = QLabel("Logs")
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: #AEB4BD;")
        outer.addWidget(title)

        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet(
            "background-color: #0F1114; border: 1px solid #262A31; "
            "border-radius: 8px; font-family: 'Consolas', monospace; color: #9AA4B2;"
        )
        outer.addWidget(self.console)

    def append_line(self, line: str):
        """Call this from MainWindow when SerialWorker.log_line fires,
        or wire up a QTimer to tail your logger.py output file."""
        self.console.appendPlainText(line)
