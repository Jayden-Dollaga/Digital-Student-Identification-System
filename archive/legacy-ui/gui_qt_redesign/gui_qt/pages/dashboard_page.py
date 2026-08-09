from PySide6.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QLabel

from gui_qt.widgets.stat_card import StatCard

# TODO: from core import database


class DashboardPage(QWidget):
    """
    Landing page: quick counts + recent activity glance.
    Pull real numbers from database.py in refresh().
    """

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

        self.card_present = StatCard("Present Today")
        self.card_absent = StatCard("Absent Today")
        self.card_total = StatCard("Total Students")
        self.card_last_scan = StatCard("Last Scan")

        grid.addWidget(self.card_present, 0, 0)
        grid.addWidget(self.card_absent, 0, 1)
        grid.addWidget(self.card_total, 0, 2)
        grid.addWidget(self.card_last_scan, 0, 3)

        outer.addLayout(grid)
        outer.addStretch()

        self.refresh()

    def refresh(self):
        # TODO: replace with real queries, e.g.
        # present = database.count_present_today()
        # absent = database.count_absent_today()
        # total = database.count_students()
        # last = database.get_last_scan()
        self.card_present.set_value("—")
        self.card_absent.set_value("—")
        self.card_total.set_value("—")
        self.card_last_scan.set_value("—")

    def on_scan_event(self, event: dict):
        """Call this from MainWindow when SerialWorker.scan_event fires."""
        self.refresh()
