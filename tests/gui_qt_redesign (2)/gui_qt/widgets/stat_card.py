from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class StatCard(QFrame):
    def __init__(self, label: str, value: str = "—", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumHeight(90)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        self._label = QLabel(label.upper())
        self._label.setObjectName("cardLabel")

        self._value = QLabel(value)
        self._value.setObjectName("cardValue")
        self._value.setAlignment(Qt.AlignLeft)

        layout.addWidget(self._label)
        layout.addWidget(self._value)
        layout.addStretch()

    def set_value(self, value: str):
        self._value.setText(value)
