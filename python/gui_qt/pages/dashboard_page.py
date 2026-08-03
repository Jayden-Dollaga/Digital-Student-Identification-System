from PySide6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QLabel

from gui_qt.widgets.stat_card import StatCard
from core.database import get_student_count, get_attendance_count_today, get_attendance_today


class DashboardPage(QWidget):
    """Landing page: quick counts + recent activity glance."""

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
        outer.addStretch()

        self.refresh()

    def refresh(self):
        try:
            self.card_present.set_value(str(get_attendance_count_today()))
            self.card_total.set_value(str(get_student_count()))

            today_rows = get_attendance_today()
            if today_rows:
                latest = today_rows[0]  # already ordered DESC by timestamp
                name = latest.get("student_name") or "Unregistered"
                self.card_last_scan.set_value(f"{name} · {latest.get('time', '')}")
            else:
                self.card_last_scan.set_value("No scans yet")
        except Exception:
            # DB not initialized yet, or called before init_database() ran
            self.card_present.set_value("—")
            self.card_total.set_value("—")
            self.card_last_scan.set_value("—")

    def on_scan_event(self, event: dict):
        """Call this from MainWindow when SerialWorker.scan_event fires."""
        self.refresh()
