from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QGridLayout, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QListWidget, QListWidgetItem,
)

from gui_qt.widgets.stat_card import StatCard
from core.database import get_student_count, get_attendance_count_today, get_today_attendance_info

MAX_HISTORY_ITEMS = 200


class DashboardPage(QWidget):
    """Landing page: quick counts + recent activity history."""

    def __init__(self, parent=None):
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(20)

        heading = QLabel("Today at a glance")
        heading.setStyleSheet("font-size: 15px; font-weight: 600; color: #AEB4BD;")
        outer.addWidget(heading)

        grid = QGridLayout()
        grid.setSpacing(16)

        self.card_present = StatCard("Scans Today")
        self.card_total = StatCard("Total Students")
        self.card_last_scan = StatCard("Last Scan")

        grid.addWidget(self.card_present, 0, 0)
        grid.addWidget(self.card_total, 0, 1)
        grid.addWidget(self.card_last_scan, 0, 2)

        outer.addLayout(grid)

        activity_card = QFrame()
        activity_card.setObjectName("card")
        activity_layout = QVBoxLayout(activity_card)
        activity_layout.setContentsMargins(16, 16, 16, 16)
        activity_layout.setSpacing(8)

        activity_header = QHBoxLayout()
        activity_title = QLabel("Recent activity")
        activity_title.setObjectName("cardLabel")
        activity_header.addWidget(activity_title)
        activity_header.addStretch()
        activity_layout.addLayout(activity_header)

        # Was a single QLabel that only ever showed the *latest* scan and
        # got overwritten every time a new one came in - previous scans
        # were gone the moment the next person scanned. This is now a
        # scrollable list holding the whole day's history (newest first),
        # same idea as before but it actually keeps the record instead of
        # replacing it.
        self.activity_list = QListWidget()
        self.activity_list.setObjectName("recentActivityList")
        self.activity_list.setFocusPolicy(Qt.NoFocus)
        self.activity_list.setStyleSheet(
            "QListWidget { background-color: transparent; border: none; }"
            "QListWidget::item { padding: 6px 2px; border-bottom: 1px solid #22262D; color: #D4D9E0; }"
        )
        self.activity_list.setMinimumHeight(220)
        activity_layout.addWidget(self.activity_list)

        self.activity_empty_label = QLabel("No attendance activity has been recorded today yet.")
        self.activity_empty_label.setWordWrap(True)
        self.activity_empty_label.setStyleSheet("color: #D4D9E0; line-height: 1.4;")
        self.activity_empty_label.setVisible(False)
        activity_layout.addWidget(self.activity_empty_label)

        self.activity_fallback_label = QLabel(
            "No scans recorded today yet — showing the most recent activity instead."
        )
        self.activity_fallback_label.setWordWrap(True)
        self.activity_fallback_label.setStyleSheet(
            "color: #F5B942; background-color: #2A2410; border: 1px solid #4A3F1A; "
            "border-radius: 6px; padding: 6px 10px;"
        )
        self.activity_fallback_label.setVisible(False)
        activity_layout.addWidget(self.activity_fallback_label)

        outer.addWidget(activity_card)
        outer.addStretch()

        self.refresh()

    def _format_item_text(self, row: dict) -> str:
        name = row.get("student_name") or "Unregistered"
        time_str = row.get("time", "")
        status = row.get("status", "")
        confidence = row.get("confidence", "")
        date_str = row.get("date", "")
        suffix = f" · {confidence}%" if confidence not in ("", None) else ""
        return f"{date_str}  {time_str}   {name}   [{status}]{suffix}"

    def refresh(self):
        try:
            self.card_present.set_value(str(get_attendance_count_today()))
            self.card_total.set_value(str(get_student_count()))

            info = get_today_attendance_info()
            rows = info["rows"]
            self.activity_fallback_label.setVisible(bool(info["is_fallback"]) and bool(rows))

            self.activity_list.clear()
            if rows:
                for row in rows[:MAX_HISTORY_ITEMS]:
                    item = QListWidgetItem(self._format_item_text(row))
                    self.activity_list.addItem(item)
                self.activity_list.setVisible(True)
                self.activity_empty_label.setVisible(False)

                latest = rows[0]  # already ordered DESC by timestamp
                name = latest.get("student_name") or "Unregistered"
                self.card_last_scan.set_value(f"{name} · {latest.get('time', '')}")
            else:
                self.activity_list.setVisible(False)
                self.activity_empty_label.setVisible(True)
                self.card_last_scan.set_value("No scans yet")
        except Exception:
            # DB not initialized yet, or called before init_database() ran
            self.card_present.set_value("—")
            self.card_total.set_value("—")
            self.card_last_scan.set_value("—")
            self.activity_list.clear()
            self.activity_list.setVisible(False)
            self.activity_fallback_label.setVisible(False)
            self.activity_empty_label.setVisible(True)
            self.activity_empty_label.setText("The dashboard is still loading. Please try again shortly.")

    def refresh_dashboard(self):
        self.refresh()

    def on_scan_event(self, event: dict):
        """Call this from MainWindow when SerialWorker.scan_event fires.

        Prepends the new scan directly instead of doing a full refresh, so
        the history list grows live the same way the Attendance page does.
        """
        self.card_present.set_value(str(get_attendance_count_today()))
        name = event.get("student_name") or "Unregistered"
        self.card_last_scan.set_value(f"{name} · {event.get('time', '')}")

        self.activity_fallback_label.setVisible(False)
        self.activity_empty_label.setVisible(False)
        self.activity_list.setVisible(True)
        item = QListWidgetItem(self._format_item_text(event))
        self.activity_list.insertItem(0, item)
        while self.activity_list.count() > MAX_HISTORY_ITEMS:
            self.activity_list.takeItem(self.activity_list.count() - 1)