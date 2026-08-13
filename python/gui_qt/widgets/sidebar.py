from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QButtonGroup, QFrame
)
from PySide6.QtCore import Signal, Qt


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
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(6)

        # ---- Brand header: logo mark + "DSIS" + full-name caption ----
        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        brand_mark = QLabel("DS")
        brand_mark.setObjectName("brandMark")
        brand_mark.setFixedSize(36, 36)
        brand_mark.setAlignment(Qt.AlignCenter)
        header_row.addWidget(brand_mark)

        title = QLabel("DSIS")
        title.setObjectName("sidebarTitle")
        header_row.addWidget(title)
        header_row.addStretch()

        layout.addLayout(header_row)

        subtitle = QLabel("Digital Student Identification System")
        subtitle.setObjectName("sidebarSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        divider = QFrame()
        divider.setObjectName("sidebarDivider")
        divider.setFrameShape(QFrame.HLine)
        divider.setFixedHeight(1)
        layout.addSpacing(10)
        layout.addWidget(divider)
        layout.addSpacing(6)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        for key, label in NAV_ITEMS:
            btn = QPushButton(label)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.setCursor(self.cursor().shape())
            btn.clicked.connect(lambda _checked, k=key: self.page_selected.emit(k))
            self._group.addButton(btn)
            layout.addWidget(btn)

        layout.addStretch()

        # default selection
        self._group.buttons()[0].setChecked(True)