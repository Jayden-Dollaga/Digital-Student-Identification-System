from datetime import datetime, timedelta

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QHeaderView, QPushButton, QComboBox
)

from core.database import get_today_attendance_info, get_attendance_paginated, export_attendance_range

COLUMNS = ["Date", "Time", "Student No.", "Name", "Grade/Section", "Confidence", "Status"]
PAGE_SIZE = 100
LAST_30_DAYS_LABEL = "Last 30 Days"


class AttendancePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._offset = 0
        self._last_page_row_count = 0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        header_row = QHBoxLayout()
        title = QLabel("Attendance")
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: #AEB4BD;")

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Today", "Recent", LAST_30_DAYS_LABEL])
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)

        self.prev_btn = QPushButton("◀ Prev")
        self.prev_btn.clicked.connect(self.on_prev_clicked)
        self.next_btn = QPushButton("Next ▶")
        self.next_btn.clicked.connect(self.on_next_clicked)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("primaryButton")
        refresh_btn.clicked.connect(self.refresh)

        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addWidget(self.mode_combo)
        header_row.addWidget(self.prev_btn)
        header_row.addWidget(self.next_btn)
        header_row.addWidget(refresh_btn)
        outer.addLayout(header_row)

        self.fallback_banner = QLabel(
            "No attendance recorded today yet — showing the most recent activity instead."
        )
        self.fallback_banner.setObjectName("warningBanner")
        self.fallback_banner.setWordWrap(True)
        self.fallback_banner.setVisible(False)
        outer.addWidget(self.fallback_banner)

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

    def _on_mode_changed(self, _text):
        self._offset = 0
        self.refresh()

    def _is_recent_mode(self) -> bool:
        return self.mode_combo.currentText() == "Recent"

    def _is_last_30_days_mode(self) -> bool:
        return self.mode_combo.currentText() == LAST_30_DAYS_LABEL

    def refresh(self):
        try:
            if self._is_last_30_days_mode():
                self.fallback_banner.setVisible(False)
                # Same date-range function the CSV export button uses, so
                # what you see here always matches what gets exported.
                end = datetime.now().strftime("%Y-%m-%d")
                start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                rows = export_attendance_range(start, end)
                rows = list(reversed(rows))  # export_attendance_range is ASC; show newest first
            elif self._is_recent_mode():
                self.fallback_banner.setVisible(False)
                rows = get_attendance_paginated(limit=PAGE_SIZE, offset=self._offset)
            else:
                info = get_today_attendance_info()
                rows = info["rows"]
                self.fallback_banner.setVisible(info["is_fallback"])
        except Exception:
            rows = []
            self.fallback_banner.setVisible(False)
        self._last_page_row_count = len(rows)
        self._populate(rows)
        self._update_pagination_controls()

    def _update_pagination_controls(self):
        recent = self._is_recent_mode()
        self.prev_btn.setVisible(recent)
        self.next_btn.setVisible(recent)
        if not recent:
            return
        self.prev_btn.setEnabled(self._offset > 0)
        self.next_btn.setEnabled(self._last_page_row_count == PAGE_SIZE)

    def on_prev_clicked(self):
        if self._offset <= 0:
            return
        self._offset = max(0, self._offset - PAGE_SIZE)
        self.refresh()

    def on_next_clicked(self):
        if self._last_page_row_count < PAGE_SIZE:
            return
        self._offset += PAGE_SIZE
        self.refresh()

    def _populate(self, rows):
        self.table.setRowCount(0)
        self.empty_label.setVisible(not rows)
        self.table.setVisible(bool(rows))
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            values = [
                row.get("date", ""),
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
        if self._is_recent_mode() and self._offset != 0:
            # Not viewing the first page - a live scan shouldn't reshuffle
            # rows the user is currently paging through.
            return
        if self.table.rowCount() == 0:
            self.table.setVisible(True)
            self.empty_label.setVisible(False)
        self.table.insertRow(0)
        values = [
            event.get("date", ""),
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
            self.table.sortItems(1, Qt.DescendingOrder)
