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

FULL_WIDTH = 200
COMPACT_WIDTH = 68


class Sidebar(QWidget):
    page_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self._compact = False
        self.setFixedWidth(FULL_WIDTH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(6)
        self._layout = layout

        # ---- Brand header: logo mark + "DSIS" + full-name caption ----
        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        brand_mark = QLabel("DS")
        brand_mark.setObjectName("brandMark")
        brand_mark.setFixedSize(36, 36)
        brand_mark.setAlignment(Qt.AlignCenter)
        header_row.addWidget(brand_mark)

        self._title = QLabel("DSIS")
        self._title.setObjectName("sidebarTitle")
        header_row.addWidget(self._title)
        header_row.addStretch()

        layout.addLayout(header_row)

        self._subtitle = QLabel("Digital Student Identification System")
        self._subtitle.setObjectName("sidebarSubtitle")
        self._subtitle.setWordWrap(True)
        layout.addWidget(self._subtitle)

        divider = QFrame()
        divider.setObjectName("sidebarDivider")
        divider.setFrameShape(QFrame.HLine)
        divider.setFixedHeight(1)
        layout.addSpacing(10)
        layout.addWidget(divider)
        layout.addSpacing(6)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._nav_buttons = {}

        for key, label in NAV_ITEMS:
            btn = QPushButton(label)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.setCursor(self.cursor().shape())
            btn.setToolTip(label)
            btn.clicked.connect(lambda _checked, k=key: self.page_selected.emit(k))
            self._group.addButton(btn)
            layout.addWidget(btn)
            self._nav_buttons[key] = (btn, label)

        layout.addStretch()

        # default selection
        self._group.buttons()[0].setChecked(True)

    def set_compact(self, compact: bool) -> None:
        """Toggle icons-only compact mode to save horizontal space."""
        compact = bool(compact)
        if compact == self._compact:
            return
        self._compact = compact
        self.setFixedWidth(COMPACT_WIDTH if compact else FULL_WIDTH)
        self._subtitle.setVisible(not compact)
        self._title.setVisible(not compact)
        for key, (btn, label) in self._nav_buttons.items():
            btn.setText(label[:1] if compact else label)

    def is_compact(self) -> bool:
        return self._compact

    def set_enabled_pages(self, allowed_keys) -> None:
        """Enable/disable nav buttons based on an iterable of permitted page keys.
        Passing None re-enables every page."""
        for key, (btn, _label) in self._nav_buttons.items():
            btn.setEnabled(True if allowed_keys is None else key in allowed_keys)
