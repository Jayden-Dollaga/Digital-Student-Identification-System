from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QButtonGroup
from PySide6.QtCore import Signal


NAV_ITEMS = [
    ("dashboard", "Dashboard"),
    ("attendance", "Attendance"),
    ("students", "Students"),
    ("reports", "Reports"),
    ("logs", "Logs"),
    ("settings", "Settings"),
]


class Sidebar(QWidget):
    page_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 12)
        layout.setSpacing(2)

        title = QLabel("Attendance")
        title.setObjectName("sidebarTitle")
        layout.addWidget(title)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        for key, label in NAV_ITEMS:
            btn = QPushButton(label)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _checked, k=key: self.page_selected.emit(k))
            self._group.addButton(btn)
            layout.addWidget(btn)

        layout.addStretch()

        # default selection
        self._group.buttons()[0].setChecked(True)
