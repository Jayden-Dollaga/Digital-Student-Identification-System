from PySide6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QLabel, QFrame

from gui_qt.widgets.stat_card import StatCard
from core.database import get_student_count, get_attendance_count_today, get_today_attendance_info


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

        activity_card = QFrame()
        activity_card.setObjectName("card")
        activity_layout = QVBoxLayout(activity_card)
        activity_layout.setContentsMargins(16, 16, 16, 16)
        activity_layout.setSpacing(8)

        activity_title = QLabel("Recent activity")
        activity_title.setObjectName("cardLabel")
        self.activity_summary = QLabel("Waiting for the next scan...")
        self.activity_summary.setWordWrap(True)
        self.activity_summary.setStyleSheet("color: #D4D9E0; line-height: 1.4;")

        activity_layout.addWidget(activity_title)
        activity_layout.addWidget(self.activity_summary)
        outer.addWidget(activity_card)
        outer.addStretch()

        self.refresh()

    def refresh(self):
        try:
            self.card_present.set_value(str(get_attendance_count_today()))
            self.card_total.set_value(str(get_student_count()))

            info = get_today_attendance_info()
            today_rows = info["rows"]
            if today_rows:
                latest = today_rows[0]  # already ordered DESC by timestamp
                name = latest.get("student_name") or "Unregistered"
                self.card_last_scan.set_value(f"{name} · {latest.get('time', '')}")
                if info["is_fallback"]:
                    self.activity_summary.setText(
                        f"No scans today yet. Most recent: {name} on {latest.get('date', '')} "
                        f"at {latest.get('time', '')} with {latest.get('confidence', 0)}% confidence."
                    )
                else:
                    self.activity_summary.setText(
                        f"Latest record: {name} at {latest.get('time', '')} with {latest.get('confidence', 0)}% confidence."
                    )
            else:
                self.card_last_scan.set_value("No scans yet")
                self.activity_summary.setText("No attendance activity has been recorded today yet.")
        except Exception:
            # DB not initialized yet, or called before init_database() ran
            self.card_present.set_value("—")
            self.card_total.set_value("—")
            self.card_last_scan.set_value("—")
            self.activity_summary.setText("The dashboard is still loading. Please try again shortly.")

    def refresh_dashboard(self):
        self.refresh()

    def on_scan_event(self, event: dict):
        """Call this from MainWindow when SerialWorker.scan_event fires."""
        self.refresh()
