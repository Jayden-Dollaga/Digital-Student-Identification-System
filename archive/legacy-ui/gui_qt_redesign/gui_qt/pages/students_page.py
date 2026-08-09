from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QHeaderView, QPushButton
)

# TODO: from core import database, commands

COLUMNS = ["Fingerprint ID", "Name", "Role", "Enrolled On"]


class StudentsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        header_row = QHBoxLayout()
        title = QLabel("Students")
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: #AEB4BD;")
        enroll_btn = QPushButton("+ Enroll Student")
        enroll_btn.setObjectName("primaryButton")
        enroll_btn.clicked.connect(self.on_enroll_clicked)
        delete_btn = QPushButton("Delete Selected")
        delete_btn.setObjectName("dangerButton")
        delete_btn.clicked.connect(self.on_delete_clicked)

        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addWidget(delete_btn)
        header_row.addWidget(enroll_btn)
        outer.addLayout(header_row)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        outer.addWidget(self.table)

        self.refresh()

    def refresh(self):
        # TODO: rows = database.get_all_students()
        rows = []
        self.table.setRowCount(0)
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            for c, value in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(str(value)))

    def on_enroll_clicked(self):
        # TODO: open an EnrollDialog, call commands.send("enroll", ...)
        pass

    def on_delete_clicked(self):
        # TODO: get selected fingerprint ID, call commands.send("delete", id=...)
        pass
