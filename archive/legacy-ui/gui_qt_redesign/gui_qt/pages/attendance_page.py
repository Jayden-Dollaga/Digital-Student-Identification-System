from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QHeaderView, QPushButton
)

# TODO: from core import database

COLUMNS = ["Time", "Student", "Confidence", "Status"]


class AttendancePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        header_row = QHBoxLayout()
        title = QLabel("Live Attendance")
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: #AEB4BD;")
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("primaryButton")
        refresh_btn.clicked.connect(self.refresh)
        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addWidget(refresh_btn)
        outer.addLayout(header_row)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        outer.addWidget(self.table)

        self.refresh()

    def refresh(self):
        # TODO: rows = database.get_attendance_history(limit=200)
        rows = []
        self._populate(rows)

    def _populate(self, rows):
        self.table.setRowCount(0)
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            for c, value in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(str(value)))

    def on_scan_event(self, event: dict):
        """Prepend a new row live when SerialWorker emits scan_event."""
        self.table.insertRow(0)
        values = [
            event.get("time", ""),
            event.get("student", ""),
            event.get("confidence", ""),
            event.get("status", ""),
        ]
        for c, value in enumerate(values):
            self.table.setItem(0, c, QTableWidgetItem(str(value)))
