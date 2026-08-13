from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QTableWidget, QTableWidgetItem,
    QLabel, QHeaderView, QPushButton, QDialog, QLineEdit, QMessageBox, QTextEdit
)
from PySide6.QtGui import QTextCursor
from PySide6.QtCore import Qt

from services.student_service import StudentService
from core.commands import cmd_enroll, cmd_delete, cmd_wipe, cmd_stop
from core.database import clear_all_data

COLUMNS = ["Fingerprint ID", "Student No.", "Name", "Grade", "Section"]


class EnrollDialog(QDialog):
    """
    Matches the real enrollment flow from gui/dialogs.py: the fingerprint ID
    is assigned by the ESP32 itself (not typed in), reported via serial as
    "ENROLLING FINGER AS ID #N" then "SUCCESS! Finger saved as ID #N".
    Save stays disabled until that success line arrives.
    """

    def __init__(self, serial_handler, serial_worker, parent=None):
        super().__init__(parent)
        self.serial_handler = serial_handler
        self.serial_worker = serial_worker
        self.assigned_id = None
        self.ready_to_save = False
        self._enrollment_started = False  # Track if enrollment has been signaled to start

        self.setWindowTitle("Enroll Fingerprint")
        self.setMinimumWidth(420)

        outer = QVBoxLayout(self)

        self.status_label = QLabel("Waiting for the sensor to capture a fingerprint.")
        self.status_label.setWordWrap(True)
        outer.addWidget(self.status_label)

        self.id_label = QLabel("Assigned ID: Pending")
        outer.addWidget(self.id_label)

        form = QFormLayout()
        self.student_no = QLineEdit()
        self.student_name = QLineEdit()
        self.grade = QLineEdit()
        self.section = QLineEdit()
        form.addRow("Student No.", self.student_no)
        form.addRow("Full Name", self.student_name)
        form.addRow("Grade", self.grade)
        form.addRow("Section", self.section)
        outer.addLayout(form)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(120)
        self.log_view.setMaximumHeight(180)
        self.log_view.setLineWrapMode(QTextEdit.WidgetWidth)
        self.log_view.setStyleSheet(
            "background-color: #0F1114; border: 1px solid #262A31; "
            "border-radius: 4px; font-family: 'Consolas', monospace; font-size: 11px; color: #9AA4B2;"
        )
        outer.addWidget(self.log_view)

        button_row = QHBoxLayout()
        self.start_btn = QPushButton("Start Enrollment")
        self.start_btn.setObjectName("primaryButton")
        self.start_btn.clicked.connect(self.on_start)
        self.save_btn = QPushButton("Save Student")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_row.addWidget(self.start_btn)
        button_row.addWidget(cancel_btn)
        button_row.addWidget(self.save_btn)
        outer.addLayout(button_row)

        self.serial_worker.enroll_progress.connect(self.on_enroll_progress)
        self.serial_worker.raw_line.connect(self._append_log_line)

    # Exact line prefixes the firmware prints during ENROLL, taken straight
    # from enrollFinger()/printHelp() in ESP32_Fingerprint_AllInOne.ino.
    # Matching prefixes (not "contains this word anywhere") is what keeps
    # this from also catching printHelp()'s static command menu, since STOP
    # (sent right before ENROLL to cancel any active scan) makes the
    # firmware reprint that whole menu and several of its lines happen to
    # contain words like "finger"/"enroll" too (e.g. "Delete finger ID 1").
    _ENROLL_PROGRESS_PREFIXES = (
        "ENROLLING FINGER AS ID",
        "STEP 1:", "STEP 2:", "STEP 3:",
        "IMAGE TAKEN!", "IMAGE CONVERTED.",
        "FINGER REMOVED.",
        "IMAGING ERROR",
        "SUCCESS! FINGER SAVED AS ID",
        "TOTAL STORED:",
        "ERROR:", "TIP:",
        "ENROLLMENT CANCELLED",
        ">> ENROLLMENT CANCELLED",
        "TYPE ENROLL:",
    )

    def _append_log_line(self, line: str):
        # Only append enrollment-specific log lines
        if not self._enrollment_started:
            return

        stripped = line.strip()
        if not stripped:
            return

        # Pure separator lines ("----------------------------------------")
        is_separator = set(stripped) == {"-"}
        is_progress_line = stripped.upper().startswith(self._ENROLL_PROGRESS_PREFIXES)

        if is_separator or is_progress_line:
            self.log_view.append(line)
            self.log_view.moveCursor(QTextCursor.End)
            self.log_view.ensureCursorVisible()

    def on_start(self):
        if not self.serial_handler.is_connected():
            QMessageBox.warning(self, "Not connected", "Connect to the ESP32 first.")
            return
        self.assigned_id = None
        self.ready_to_save = False
        self.id_label.setText("Assigned ID: Pending")
        self.save_btn.setEnabled(False)
        self.log_view.clear()  # Clear previous logs
        self._enrollment_started = True  # Start capturing enrollment-specific lines
        cmd_stop(self.serial_handler)  # stop any active scan mode first, same as app.py's enroll_sample()
        if cmd_enroll(self.serial_handler):
            self.status_label.setText("Sent ENROLL command. Follow the prompts on the sensor.")
            self.start_btn.setEnabled(False)
        else:
            self._enrollment_started = False  # Stop capturing if command failed
            QMessageBox.critical(self, "Failed", "Could not send ENROLL command to the ESP32.")

    def on_enroll_progress(self, progress: dict):
        event = progress.get("event")
        if event == "enrolling":
            self.assigned_id = progress.get("id")
            self.ready_to_save = False
            self.save_btn.setEnabled(False)
            self.id_label.setText(f"Assigned ID: {self.assigned_id}")
            self.status_label.setText("Enrolling — follow the prompts on the sensor. Save is disabled until enrollment completes.")
        elif event == "success":
            self._enrollment_started = False  # Stop capturing logs
            self.assigned_id = progress.get("id")
            self.ready_to_save = True
            self.save_btn.setEnabled(True)
            self.id_label.setText(f"Assigned ID: {self.assigned_id}")
            self.status_label.setText(f"Fingerprint saved as ID {self.assigned_id}. Fill in the student's details and Save.")
        elif event == "cancelled":
            self._enrollment_started = False  # Stop capturing logs
            self.ready_to_save = False
            self.save_btn.setEnabled(False)
            self.status_label.setText("Enrollment cancelled. Start a new enrollment to try again.")
            self.start_btn.setEnabled(True)
        elif event == "error":
            self._enrollment_started = False  # Stop capturing logs
            self.status_label.setText("Sensor reported an error — check the log below.")

    def accept(self):
        if not self.ready_to_save or not self.assigned_id:
            QMessageBox.warning(self, "Missing fingerprint", "The fingerprint has not been enrolled yet.")
            return
        if not all([self.student_no.text().strip(), self.student_name.text().strip(),
                    self.grade.text().strip(), self.section.text().strip()]):
            QMessageBox.warning(self, "Incomplete details", "Please fill in student number, name, grade, and section.")
            return
        super().accept()

    def get_values(self):
        return {
            "fingerprint_id": int(self.assigned_id),
            "student_no": self.student_no.text().strip(),
            "student_name": self.student_name.text().strip(),
            "grade": self.grade.text().strip(),
            "section": self.section.text().strip(),
        }

    def closeEvent(self, event):
        self._enrollment_started = False  # Stop capturing logs
        try:
            self.serial_worker.enroll_progress.disconnect(self.on_enroll_progress)
            self.serial_worker.raw_line.disconnect(self._append_log_line)
        except (RuntimeError, TypeError):
            pass
        if self.serial_handler.is_connected():
            cmd_stop(self.serial_handler)
        super().closeEvent(event)


class StudentDetailsDialog(QDialog):
    """Edit/create a student profile for a known fingerprint ID."""

    def __init__(self, fingerprint_id: int, existing=None, parent=None):
        super().__init__(parent)
        self.fingerprint_id = fingerprint_id
        self.existing = existing or {}

        self.setWindowTitle(f"Student Profile — ID {fingerprint_id}")
        self.setMinimumWidth(420)

        outer = QVBoxLayout(self)
        form = QFormLayout()
        self.student_no = QLineEdit(self.existing.get("student_no", ""))
        self.student_name = QLineEdit(self.existing.get("student_name", ""))
        self.grade = QLineEdit(self.existing.get("grade", ""))
        self.section = QLineEdit(self.existing.get("section", ""))
        form.addRow("Fingerprint ID", QLabel(str(fingerprint_id)))
        form.addRow("Student No.", self.student_no)
        form.addRow("Full Name", self.student_name)
        form.addRow("Grade", self.grade)
        form.addRow("Section", self.section)
        outer.addLayout(form)

        buttons = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons.addStretch()
        buttons.addWidget(cancel_btn)
        buttons.addWidget(save_btn)
        outer.addLayout(buttons)

    def get_values(self):
        return {
            "fingerprint_id": self.fingerprint_id,
            "student_no": self.student_no.text().strip(),
            "student_name": self.student_name.text().strip(),
            "grade": self.grade.text().strip(),
            "section": self.section.text().strip(),
        }


class WipeDialog(QDialog):
    """Matches gui/dialogs.py's open_wipe_dialog / confirm_wipe flow."""

    def __init__(self, serial_handler, serial_worker, on_wiped, parent=None):
        super().__init__(parent)
        self.serial_handler = serial_handler
        self.serial_worker = serial_worker
        self.on_wiped = on_wiped

        self.setWindowTitle("Confirm Wipe")
        self.setMinimumWidth(420)

        outer = QVBoxLayout(self)
        warning = QLabel(
            "This removes ALL stored fingerprints from the ESP32 and clears the "
            "linked student and attendance data from the local database."
        )
        warning.setWordWrap(True)
        outer.addWidget(warning)

        self.status_label = QLabel("This will erase stored fingerprints and clear related database records.")
        self.status_label.setWordWrap(True)
        outer.addWidget(self.status_label)

        button_row = QHBoxLayout()
        self.confirm_btn = QPushButton("Confirm Wipe")
        self.confirm_btn.setObjectName("dangerButton")
        self.confirm_btn.clicked.connect(self.on_confirm)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_row.addWidget(self.confirm_btn)
        button_row.addWidget(cancel_btn)
        outer.addLayout(button_row)

        self.serial_worker.wipe_progress.connect(self.on_wipe_progress)

    def on_confirm(self):
        if not self.serial_handler.is_connected():
            self.status_label.setText("Connect to the ESP32 before wiping.")
            return
        self.confirm_btn.setEnabled(False)
        self.status_label.setText("Sending wipe command to the ESP32. Please wait for confirmation.")
        if not cmd_wipe(self.serial_handler):
            self.confirm_btn.setEnabled(True)
            self.status_label.setText("Failed to send the wipe command. Check the serial connection and try again.")

    def on_wipe_progress(self, progress: dict):
        event = progress.get("event")
        if event == "start":
            self.status_label.setText("Wiping… please wait.")
        elif event == "success":
            student_count, attendance_count = clear_all_data()
            self.status_label.setText(
                f"All fingerprints wiped. Cleared {student_count} student profile(s) and "
                f"{attendance_count} attendance record(s)."
            )
            self.confirm_btn.setEnabled(True)
            if self.on_wiped:
                self.on_wiped()
        elif event == "error":
            self.status_label.setText("Sensor reported an error — check the Logs page.")
            self.confirm_btn.setEnabled(True)

    def closeEvent(self, event):
        try:
            self.serial_worker.wipe_progress.disconnect(self.on_wipe_progress)
        except (RuntimeError, TypeError):
            pass
        super().closeEvent(event)


class StudentsPage(QWidget):
    def __init__(self, serial_handler=None, serial_worker=None, parent=None):
        super().__init__(parent)
        self.serial_handler = serial_handler
        self.serial_worker = serial_worker
        self.service = StudentService()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        header_row = QHBoxLayout()
        title = QLabel("Students")
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: #AEB4BD;")
        enroll_btn = QPushButton("+ Enroll Student")
        enroll_btn.setObjectName("primaryButton")
        enroll_btn.clicked.connect(self.on_enroll_clicked)
        edit_btn = QPushButton("Edit Selected")
        edit_btn.setObjectName("secondaryButton")
        edit_btn.clicked.connect(self.on_edit_clicked)
        delete_btn = QPushButton("Delete Selected")
        delete_btn.setObjectName("dangerButton")
        delete_btn.clicked.connect(self.on_delete_clicked)
        wipe_btn = QPushButton("Wipe All Fingerprints")
        wipe_btn.setObjectName("dangerButton")
        wipe_btn.clicked.connect(self.on_wipe_clicked)

        header_row.addWidget(title)
        header_row.addStretch()
        header_row.addWidget(wipe_btn)
        header_row.addWidget(delete_btn)
        header_row.addWidget(edit_btn)
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
        try:
            rows = self.service.get_all_students()
        except Exception:
            rows = []
        self.table.setRowCount(0)
        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            values = [
                row.get("fingerprint_id", ""),
                row.get("student_no", ""),
                row.get("student_name", ""),
                row.get("grade", ""),
                row.get("section", ""),
            ]
            for c, value in enumerate(values):
                self.table.setItem(r, c, QTableWidgetItem(str(value)))

    def save_student_details(self, fingerprint_id: int, values: dict):
        student_no = values.get("student_no", "").strip() or f"ID{fingerprint_id}"
        student_name = values.get("student_name", "").strip() or f"Student {fingerprint_id}"
        grade = values.get("grade", "").strip() or "N/A"
        section = values.get("section", "").strip() or "N/A"
        ok, msg = self.service.save_student(fingerprint_id, student_no, student_name, grade, section)
        if ok:
            self.refresh()
        return ok, msg

    def on_enroll_clicked(self):
        window = self.window()
        if hasattr(window, "_set_scan_block_reason"):
            window._set_scan_block_reason("A fingerprint enrollment is currently active. Finish or cancel it before scanning.")
        dialog = EnrollDialog(self.serial_handler, self.serial_worker, parent=self)
        try:
            if dialog.exec():
                values = dialog.get_values()
                ok, msg = self.save_student_details(values["fingerprint_id"], values)
                if not ok:
                    QMessageBox.critical(self, "Save failed", msg)
        finally:
            if hasattr(window, "_clear_scan_block_reason"):
                window._clear_scan_block_reason()

    def on_delete_clicked(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "No selection", "Select a student row first.")
            return
        fingerprint_id = int(self.table.item(row, 0).text())
        confirm = QMessageBox.question(
            self, "Confirm delete",
            f"Delete student with fingerprint ID {fingerprint_id}? "
            "This does NOT remove the fingerprint from the device — use 'Delete' on the device separately if needed."
        )
        if confirm != QMessageBox.Yes:
            return
        self.service.delete_student(fingerprint_id)
        if self.serial_handler is not None and self.serial_handler.is_connected():
            cmd_delete(self.serial_handler, fingerprint_id)
        self.refresh()

    def on_edit_clicked(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "No selection", "Select a student row first.")
            return
        fingerprint_id = int(self.table.item(row, 0).text())
        existing = self.service.get_student(fingerprint_id) or {}
        dialog = StudentDetailsDialog(fingerprint_id, existing=existing, parent=self)
        if dialog.exec() == QDialog.Accepted:
            values = dialog.get_values()
            ok, msg = self.save_student_details(values["fingerprint_id"], values)
            if not ok:
                QMessageBox.critical(self, "Save failed", msg)

    def on_wipe_clicked(self):
        window = self.window()
        if hasattr(window, "_set_scan_block_reason"):
            window._set_scan_block_reason("A wipe operation is currently active. Finish it before scanning.")
        dialog = WipeDialog(self.serial_handler, self.serial_worker, on_wiped=self.refresh, parent=self)
        try:
            dialog.exec()
        finally:
            if hasattr(window, "_clear_scan_block_reason"):
                window._clear_scan_block_reason()