import csv
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QPlainTextEdit,
    QFileDialog, QMessageBox
)

from core.database import (
    generate_statistics_report, export_attendance_range, backup_database, restore_database,
)


class ReportsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        header_row = QHBoxLayout()
        title = QLabel("Reports")
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: #AEB4BD;")

        export_btn = QPushButton("Export CSV (last 30 days)")
        export_btn.setObjectName("primaryButton")
        export_btn.clicked.connect(self.on_export_clicked)

        backup_btn = QPushButton("Backup DB")
        backup_btn.clicked.connect(self.on_backup_clicked)

        restore_btn = QPushButton("Restore DB")
        restore_btn.clicked.connect(self.on_restore_clicked)

        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addWidget(backup_btn)
        header_row.addWidget(restore_btn)
        header_row.addWidget(export_btn)
        outer.addLayout(header_row)

        self.report_view = QPlainTextEdit()
        self.report_view.setReadOnly(True)
        self.report_view.setStyleSheet(
            "background-color: #0F1114; border: 1px solid #262A31; "
            "border-radius: 8px; font-family: 'Consolas', monospace; color: #9AA4B2;"
        )
        outer.addWidget(self.report_view)

        self.refresh()

    def refresh(self):
        try:
            report_text = generate_statistics_report()
        except Exception as exc:
            report_text = f"Could not generate report: {exc}"
        self.report_view.setPlainText(report_text)

    def on_export_clicked(self):
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        try:
            rows = export_attendance_range(start, end)
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", str(exc))
            return

        if not rows:
            QMessageBox.information(self, "Export", "No attendance records in the last 30 days.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "attendance_export.csv", "CSV Files (*.csv)")
        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        QMessageBox.information(self, "Export complete", f"Saved {len(rows)} records to {path}")

    def on_backup_clicked(self):
        ok, msg, path = backup_database()
        if ok:
            QMessageBox.information(self, "Backup", msg)
        else:
            QMessageBox.critical(self, "Backup failed", msg)

    def on_restore_clicked(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select backup file", "", "Database Files (*.db)")
        if not path:
            return
        confirm = QMessageBox.question(
            self, "Confirm restore",
            "This will overwrite the current database with the selected backup. Continue?"
        )
        if confirm != QMessageBox.Yes:
            return
        ok, msg = restore_database(path)
        if ok:
            QMessageBox.information(self, "Restore", msg)
            self.refresh()
        else:
            QMessageBox.critical(self, "Restore failed", msg)
