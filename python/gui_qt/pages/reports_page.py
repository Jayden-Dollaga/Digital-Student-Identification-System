import csv
from datetime import datetime, timedelta
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QPlainTextEdit,
    QFileDialog, QMessageBox, QListWidget, QListWidgetItem
)

from config import DB_PATH
from core.database import (
    generate_statistics_report, export_attendance_range, backup_database, restore_database,
    list_backups,
)
from core.logger import log

# Leading characters that spreadsheet apps (Excel, LibreOffice, Google
# Sheets) treat as the start of a formula when a CSV cell is opened.
_FORMULA_TRIGGER_CHARS = ("=", "+", "-", "@", "\t", "\r")


def _sanitize_csv_cell(value):
    """Neutralize CSV/formula-injection payloads (CWE-1236) before writing.

    student_no / student_name / grade / section are free-text fields typed
    into the Add/Edit Student forms with no restriction on leading
    characters. If a value starts with '=', '+', '-', or '@', Excel and
    similar tools interpret the cell as a formula when the exported file is
    opened — which can range from a junk calculation to (on older Excel
    versions, via DDE) code execution. Prefixing such values with a single
    quote forces spreadsheet apps to treat them as plain text while leaving
    the value visually unchanged for anyone reading the CSV as text.
    """
    text = "" if value is None else str(value)
    if text.startswith(_FORMULA_TRIGGER_CHARS):
        return "'" + text
    return text


class ReportsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        header_row = QHBoxLayout()
        title = QLabel("Reports")
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: #AEB4BD;")

        intro_label = QLabel("Report preview")
        intro_label.setObjectName("cardLabel")

        export_btn = QPushButton("Export CSV (last 30 days)")
        export_btn.setObjectName("primaryButton")
        export_btn.clicked.connect(self.on_export_clicked)

        backup_btn = QPushButton("Backup DB")
        backup_btn.setObjectName("secondaryButton")
        backup_btn.clicked.connect(self.on_backup_clicked)

        restore_btn = QPushButton("Restore DB")
        restore_btn.setObjectName("secondaryButton")
        restore_btn.clicked.connect(self.on_restore_clicked)

        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addWidget(intro_label)
        header_row.addWidget(backup_btn)
        header_row.addWidget(restore_btn)
        header_row.addWidget(export_btn)
        outer.addLayout(header_row)

        self.report_view = QPlainTextEdit()
        self.report_view.setObjectName("reportView")
        self.report_view.setPlaceholderText("Statistics will appear here as soon as the report is generated.")
        self.report_view.setReadOnly(True)
        outer.addWidget(self.report_view)

        backups_header = QHBoxLayout()
        backups_title = QLabel("Recent Backups")
        backups_title.setObjectName("cardLabel")
        self.backups_caption = QLabel("")
        self.backups_caption.setObjectName("mutedLabel")
        backups_header.addWidget(backups_title)
        backups_header.addStretch()
        backups_header.addWidget(self.backups_caption)
        outer.addLayout(backups_header)

        # Shows both manual ("Backup DB") and automatic backups in the same
        # list, newest first - this is the easiest way to actually confirm
        # automatic backups are running rather than just trusting the logs.
        self.backups_list = QListWidget()
        self.backups_list.setObjectName("backupsList")
        self.backups_list.setMaximumHeight(140)
        outer.addWidget(self.backups_list)

        self.refresh()

    def refresh_backup_list(self):
        try:
            backups = list_backups()
        except Exception as exc:
            log.error(f"Could not list backups: {exc}")
            backups = []

        self.backups_list.clear()
        if not backups:
            self.backups_caption.setText("No backups yet")
            item = QListWidgetItem("No backups yet - click \"Backup DB\" or wait for the automatic backup.")
            self.backups_list.addItem(item)
            return

        self.backups_caption.setText(f"{len(backups)} backup(s)")
        for entry in backups:
            item = QListWidgetItem(f"{entry['date']}   {entry['name']}   ({entry['size_mb']})")
            self.backups_list.addItem(item)

    def refresh(self):
        try:
            report_text = generate_statistics_report()
        except Exception as exc:
            log.error(f"Could not generate statistics report: {exc}")
            report_text = "Unable to generate the report. Please check the application logs for more information."
        self.report_view.setPlainText(report_text)
        self.refresh_backup_list()

    def refresh_report(self):
        self.refresh()

    def on_export_clicked(self):
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        try:
            rows = export_attendance_range(start, end)
        except Exception as exc:
            log.error(f"Could not export attendance range ({start} to {end}): {exc}")
            QMessageBox.critical(
                self,
                "Export failed",
                "Unable to export the report. Please check the application logs for more information.",
            )
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
            for row in rows:
                writer.writerow({key: _sanitize_csv_cell(value) for key, value in row.items()})

        QMessageBox.information(self, "Export complete", f"Saved {len(rows)} records to {path}")

    def on_backup_clicked(self):
        ok, msg, path = backup_database()
        if ok:
            QMessageBox.information(self, "Backup", msg)
            self.refresh_backup_list()
        else:
            QMessageBox.critical(self, "Backup failed", msg)

    def on_restore_clicked(self):
        # Restores are only accepted from the backups directory (see
        # restore_database's path-containment check), so start the picker
        # there instead of leaving the user to stumble onto a rejected file.
        backups_dir = Path(DB_PATH).parent / "backups"
        backups_dir.mkdir(parents=True, exist_ok=True)
        path, _ = QFileDialog.getOpenFileName(
            self, "Select backup file", str(backups_dir), "Database Files (*.db)"
        )
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
