from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout

# TODO: from core import database


class ReportsPage(QWidget):
    """
    Statistics/export page. Recommend adding a chart here later with
    QtCharts (PySide6.QtCharts) for attendance trends over time —
    keeps everything in Qt with no extra dependency.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        header_row = QHBoxLayout()
        title = QLabel("Reports")
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: #AEB4BD;")
        export_btn = QPushButton("Export CSV")
        export_btn.setObjectName("primaryButton")
        export_btn.clicked.connect(self.on_export_clicked)
        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addWidget(export_btn)
        outer.addLayout(header_row)

        placeholder = QLabel("Attendance trend chart goes here.")
        placeholder.setStyleSheet("color: #565C66;")
        outer.addWidget(placeholder)
        outer.addStretch()

    def on_export_clicked(self):
        # TODO: database.export_report(path)
        pass
