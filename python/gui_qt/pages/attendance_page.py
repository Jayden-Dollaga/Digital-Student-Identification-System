from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QHeaderView, QPushButton, QComboBox
)

from core.database import get_attendance_today, get_attendance_paginated

COLUMNS = ["Time", "Student No.", "Name", "Grade/Section", "Confidence", "Status"]
PAGE_SIZE = 100


class AttendancePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._offset = 0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        header_row = QHBoxLayout()
        title = QLabel("Attendance")
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: #AEB4BD;")

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Today", "Recent"])
        self.mode_combo.currentTextChanged.connect(lambda _: self.refresh())

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("primaryButton")
        refresh_btn.clicked.connect(self.refresh)

        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addWidget(self.mode_combo)
        header_row.addWidget(refresh_btn)
        outer.addLayout(header_row)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        outer.addWidget(self.table)

        self.empty_label = QLabel("No attendance records yet.")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setWordWrap(True)
        self.empty_label.setVisible(False)
        self.empty_label.setStyleSheet("color: #7D8798; padding: 24px;")
        outer.addWidget(self.empty_label)

        self.refresh()

    def refresh(self):
        try:
            if self.mode_combo.currentText() == "Today":
                rows = get_attendance_today()
            else:
                self._offset = 0
                rows = get_attendance_paginated(limit=PAGE_SIZE, offset=self._offset)
        except Exception:
            rows = []
        self._populate(rows)

    def _populate(self, rows):
        self.table.setRowCount(0)
        self.empty_label.setVisible(not rows)
        self.table.setVisible(bool(rows))
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            values = [
                row.get("time", ""),
                row.get("student_no", "N/A"),
                row.get("student_name", "Unknown"),
                f"{row.get('grade', 'N/A')} / {row.get('section', 'N/A')}",
                row.get("confidence", ""),
                row.get("status", ""),
            ]
            for c, value in enumerate(values):
                self.table.setItem(r, c, QTableWidgetItem(str(value)))

    def on_scan_event(self, event: dict):
        """Prepend a new row live when SerialWorker emits scan_event, without a full refresh."""
        if self.table.rowCount() == 0:
            self.table.setVisible(True)
            self.empty_label.setVisible(False)
        self.table.insertRow(0)
        values = [
            event.get("time", ""),
            event.get("student_no", "N/A"),
            event.get("student_name", "Unknown"),
            f"{event.get('grade', 'N/A')} / {event.get('section', 'N/A')}",
            event.get("confidence", ""),
            event.get("status", ""),
        ]
        for c, value in enumerate(values):
            self.table.setItem(0, c, QTableWidgetItem(str(value)))
        if self.table.rowCount() > 1:
            self.table.sortItems(0, Qt.DescendingOrder)
