from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QTableWidget, QTableWidgetItem,
    QLabel, QHeaderView, QPushButton, QDialog, QLineEdit, QMessageBox, QTextEdit
)
from PySide6.QtGui import QTextCursor
from PySide6.QtCore import Qt
from enum import Enum

from services.student_service import StudentService
from core.commands import cmd_enroll, cmd_delete, cmd_wipe, cmd_stop
from core.database import clear_all_data, validate_student_input
from core.logger import log

COLUMNS = ["Fingerprint ID", "Student No.", "Name", "Grade", "Section"]


class EnrollmentState(Enum):
    """Explicit state machine for enrollment dialog."""
    INITIAL = "initial"  # Initial state, waiting for user to fill form and click Start
    ENROLLING = "enrolling"  # Enrollment in progress on the hardware
    ENROLLMENT_SUCCESS = "success"  # Fingerprint enrolled, ready to save student record
    SAVING = "saving"  # Saving student record to database


class EnrollDialog(QDialog):
    """
    Matches the real enrollment flow from gui/dialogs.py: the fingerprint ID
    is assigned by the ESP32 itself (not typed in), reported via serial as
    "ENROLLING FINGER AS ID #N" then "SUCCESS! Finger saved as ID #N".
    
    Uses a single primary action button that changes label and behavior based on state:
    - INITIAL: "Start Enrollment" (enabled when form is valid)
    - ENROLLING: "Enrolling..." (disabled)
    - ENROLLMENT_SUCCESS: "Save Student" (enabled)
    - SAVING: "Saving..." (disabled)
    """

    def __init__(self, serial_handler, serial_worker, parent=None):
        super().__init__(parent)
        self.serial_handler = serial_handler
        self.serial_worker = serial_worker
        
        # State machine
        self.state = EnrollmentState.INITIAL
        
        # Data
        self.assigned_id = None
        self._enrollment_started = False  # Track if enrollment has been signaled to start
        self._saving_in_progress = False  # Prevent duplicate save submissions
        
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
        self.field_feedback_labels = {}
        self.validation_status = QLabel("")
        self.validation_status.setWordWrap(True)
        self.validation_status.setVisible(False)
        self.validation_status.setStyleSheet(
            "color: #F0B429; font-size: 11px; font-weight: 600; margin-top: 4px;"
        )
        
        field_containers = {
            "student_no": ("Student No.", self.student_no),
            "student_name": ("Full Name", self.student_name),
            "grade": ("Grade", self.grade),
            "section": ("Section", self.section),
        }
        for field_name, (label_text, field) in field_containers.items():
            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(4)
            layout.addWidget(field)
            feedback = QLabel("")
            feedback.setWordWrap(True)
            feedback.setVisible(False)
            feedback.setStyleSheet(
                "color: #F0B429; font-size: 11px; font-weight: 600;"
            )
            layout.addWidget(feedback)
            self.field_feedback_labels[field_name] = feedback
            form.addRow(label_text, widget)
        
        # Connect text change signals to validate form live
        for field in (self.student_no, self.student_name, self.grade, self.section):
            field.textChanged.connect(self._on_form_changed)
        
        outer.addLayout(form)
        outer.addWidget(self.validation_status)
        self._show_field_validation_feedback()

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

        # Single primary action button that changes based on state
        button_row = QHBoxLayout()
        self.primary_btn = QPushButton("Start Enrollment")
        self.primary_btn.setObjectName("primaryButton")
        self.primary_btn.setEnabled(False)  # Disabled until form is valid
        self.primary_btn.setMinimumWidth(140)
        self.primary_btn.clicked.connect(self._on_primary_action)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.setMinimumWidth(140)
        cancel_btn.clicked.connect(self.on_cancel)
        
        button_row.addWidget(cancel_btn)
        button_row.addStretch()
        button_row.addWidget(self.primary_btn)
        outer.addLayout(button_row)

        # Connect signals
        self.serial_worker.enroll_progress.connect(self.on_enroll_progress)
        self.serial_worker.raw_line.connect(self._append_log_line)
    
    def _show_field_validation_feedback(self):
        """Show live validation feedback under each field and a summary status."""
        from core.database import get_student_field_feedback

        feedback = get_student_field_feedback(
            1,
            self.student_no.text(),
            self.student_name.text(),
            self.grade.text(),
            self.section.text(),
        )

        for field_name, label in self.field_feedback_labels.items():
            result = feedback.get(field_name)
            if result is None or result.valid:
                label.setText("✓ Valid")
                label.setStyleSheet("color: #5EE6A9; font-size: 11px; font-weight: 600;")
                label.setVisible(True)
            else:
                label.setText(f"⚠ {result.message}")
                label.setStyleSheet("color: #F0B429; font-size: 11px; font-weight: 600;")
                label.setVisible(True)

        valid_fields = all(result.valid for result in feedback.values())
        if valid_fields:
            self.validation_status.setText("✓ Student information is valid")
            self.validation_status.setStyleSheet("color: #5EE6A9; font-size: 11px; font-weight: 600; margin-top: 4px;")
            self.validation_status.setVisible(True)
            return

        for field_name in ("student_no", "student_name", "grade", "section"):
            result = feedback.get(field_name)
            if result is not None and not result.valid:
                self.validation_status.setText(f"⚠ {result.message}")
                self.validation_status.setStyleSheet("color: #F0B429; font-size: 11px; font-weight: 600; margin-top: 4px;")
                self.validation_status.setVisible(True)
                return
        self.validation_status.setVisible(False)

    def _is_form_valid(self) -> bool:
        """Check if student form has valid data using the existing validation function."""
        # We don't have a fingerprint ID yet, so use a temporary valid ID for validation
        # The actual ID will come from the ESP32 after enrollment
        temp_id = 1  # Placeholder for validation purposes
        
        is_valid, _ = validate_student_input(
            temp_id,
            self.student_no.text(),
            self.student_name.text(),
            self.grade.text(),
            self.section.text()
        )
        return is_valid
    
    def _on_form_changed(self):
        """Called when any form field changes. Update button enable state if in INITIAL state."""
        self._show_field_validation_feedback()
        if self.state == EnrollmentState.INITIAL:
            self.primary_btn.setEnabled(self._is_form_valid())
    
    def _set_state(self, new_state: EnrollmentState):
        """Change the internal state and update UI accordingly."""
        self.state = new_state
        
        if new_state == EnrollmentState.INITIAL:
            self.primary_btn.setText("Start Enrollment")
            self.primary_btn.setEnabled(self._is_form_valid())
        
        elif new_state == EnrollmentState.ENROLLING:
            self.primary_btn.setText("Enrolling...")
            self.primary_btn.setEnabled(False)
        
        elif new_state == EnrollmentState.ENROLLMENT_SUCCESS:
            self.primary_btn.setText("Save Student")
            self.primary_btn.setEnabled(True)
        
        elif new_state == EnrollmentState.SAVING:
            self.primary_btn.setText("Saving...")
            self.primary_btn.setEnabled(False)
    
    def _on_primary_action(self):
        """Handle primary action button click. Action depends on current state."""
        log.debug("EnrollDialog: _on_primary_action() called", current_state=str(self.state))
        
        if self.state == EnrollmentState.INITIAL:
            log.debug("EnrollDialog: Dispatching to _start_enrollment()")
            self._start_enrollment()
        elif self.state == EnrollmentState.ENROLLMENT_SUCCESS:
            log.debug("EnrollDialog: Dispatching to _save_student()")
            self._save_student()
    
    def _start_enrollment(self):
        """Start the fingerprint enrollment process."""
        log.debug("EnrollDialog: _start_enrollment() called", state=str(self.state))
        
        try:
            if not self.serial_handler.is_connected():
                log.warning("EnrollDialog: Serial handler not connected")
                QMessageBox.warning(self, "Not connected", "Connect to the ESP32 first.")
                return
            
            # Final validation before starting enrollment
            form_valid = self._is_form_valid()
            if not form_valid:
                log.warning("EnrollDialog: Form validation failed")
                QMessageBox.warning(self, "Invalid input", "Please fill in all student fields with valid data.")
                return
            
            log.info("EnrollDialog: Resetting enrollment state variables")
            self.assigned_id = None
            self.id_label.setText("Assigned ID: Pending")
            self.log_view.clear()
            self._enrollment_started = True
            
            # Start enrollment
            log.info("EnrollDialog: Transitioning to ENROLLING state")
            self._set_state(EnrollmentState.ENROLLING)
            
            log.info("EnrollDialog: Calling cmd_stop()")
            cmd_stop(self.serial_handler)  # Stop any active scan first
            
            log.info("EnrollDialog: Calling cmd_enroll()")
            enroll_result = cmd_enroll(self.serial_handler)
            log.info(f"EnrollDialog: cmd_enroll() returned {enroll_result}")
            
            if enroll_result:
                log.info("EnrollDialog: cmd_enroll succeeded, updating status label")
                self.status_label.setText("Sent ENROLL command. Follow the prompts on the sensor.")
            else:
                log.error("EnrollDialog: cmd_enroll() returned False")
                self._enrollment_started = False
                self._set_state(EnrollmentState.INITIAL)
                QMessageBox.critical(self, "Failed", "Could not send ENROLL command to the ESP32.")
        except Exception as e:
            log.error(f"EnrollDialog: Exception in _start_enrollment: {type(e).__name__}: {e}", exc_info=True)
            self._enrollment_started = False
            self._set_state(EnrollmentState.INITIAL)
            QMessageBox.critical(self, "Error", f"An error occurred during enrollment startup: {str(e)}")
    
    def _save_student(self):
        """Save the student record to the database after successful enrollment."""
        if self._saving_in_progress:
            return  # Prevent duplicate submissions
        
        if not self.assigned_id:
            QMessageBox.warning(self, "Missing fingerprint", "The fingerprint has not been enrolled yet.")
            return
        
        # Final validation before saving
        if not self._is_form_valid():
            QMessageBox.warning(self, "Invalid input", "Please fill in all student fields with valid data.")
            return
        
        self._saving_in_progress = True
        self._set_state(EnrollmentState.SAVING)
        
        try:
            from services.student_service import StudentService
            service = StudentService()
            ok, msg = service.save_student(
                int(self.assigned_id),
                self.student_no.text().strip(),
                self.student_name.text().strip(),
                self.grade.text().strip(),
                self.section.text().strip()
            )
            
            if ok:
                self._cleanup_before_close()
                self.accept()
            else:
                self._saving_in_progress = False
                self._set_state(EnrollmentState.ENROLLMENT_SUCCESS)
                QMessageBox.critical(self, "Save failed", f"Could not save student: {msg}")
        except Exception as e:
            self._saving_in_progress = False
            self._set_state(EnrollmentState.ENROLLMENT_SUCCESS)
            QMessageBox.critical(self, "Error", f"An error occurred while saving: {str(e)}")

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

    def on_enroll_progress(self, progress: dict):
        """Handle progress events from the fingerprint sensor."""
        event = progress.get("event")
        
        if event == "enrolling":
            # Enrollment started on the hardware
            self.assigned_id = progress.get("id")
            self.id_label.setText(f"Assigned ID: {self.assigned_id}")
            self.status_label.setText("Enrolling — follow the prompts on the sensor.")
            # Already in ENROLLING state from _start_enrollment
        
        elif event == "success":
            # Fingerprint successfully enrolled, now ready to save student record
            self._enrollment_started = False  # Stop capturing logs
            self.assigned_id = progress.get("id")
            self.id_label.setText(f"Assigned ID: {self.assigned_id}")
            self.status_label.setText(f"Fingerprint saved as ID {self.assigned_id}. Fill in the student's details and Save.")
            self._set_state(EnrollmentState.ENROLLMENT_SUCCESS)
        
        elif event == "cancelled":
            # User cancelled the enrollment process
            self._enrollment_started = False  # Stop capturing logs
            self.status_label.setText("Enrollment cancelled. Start a new enrollment to try again.")
            self._set_state(EnrollmentState.INITIAL)
        
        elif event == "error":
            # Sensor reported an error
            self._enrollment_started = False  # Stop capturing logs
            self.status_label.setText("Sensor reported an error — check the log below.")
            self._set_state(EnrollmentState.INITIAL)

    def _cleanup_before_close(self):
        """Shared teardown for both Cancel and the window's X button: stop
        the device if an enrollment might still be in progress, and detach
        signal handlers so this dialog stops reacting after it's gone."""
        self._enrollment_started = False
        try:
            self.serial_worker.enroll_progress.disconnect(self.on_enroll_progress)
            self.serial_worker.raw_line.disconnect(self._append_log_line)
        except (RuntimeError, TypeError):
            pass
        if self.serial_handler.is_connected():
            cmd_stop(self.serial_handler)

    def on_cancel(self):
        self._cleanup_before_close()
        self.reject()

    def get_values(self):
        return {
            "fingerprint_id": int(self.assigned_id),
            "student_no": self.student_no.text().strip(),
            "student_name": self.student_name.text().strip(),
            "grade": self.grade.text().strip(),
            "section": self.section.text().strip(),
        }

    def closeEvent(self, event):
        self._cleanup_before_close()
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
        # Mirrors EnrollDialog's _enrollment_started guard: only treat a
        # "wipe succeeded" line from the ESP32 as real once *this* dialog
        # has actually sent WIPE. Without this, wipe_progress is connected
        # the moment the dialog opens, so any stray success line arriving
        # late from a previous session (e.g. WIPE was sent, then the app
        # closed/crashed before the confirmation line arrived, then the
        # user reopens this dialog on the next run) would silently trigger
        # clear_all_data() and erase every student/attendance record with
        # no confirmation click in the current session.
        self._wipe_requested = False

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
        if cmd_wipe(self.serial_handler):
            self._wipe_requested = True
        else:
            self.confirm_btn.setEnabled(True)
            self.status_label.setText("Failed to send the wipe command. Check the serial connection and try again.")

    def on_wipe_progress(self, progress: dict):
        if not self._wipe_requested:
            return
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
        device_connected = self.serial_handler is not None and self.serial_handler.is_connected()
        if device_connected:
            confirm_text = (
                f"Delete student with fingerprint ID {fingerprint_id}? "
                "This will also remove the fingerprint from the connected device."
            )
        else:
            confirm_text = (
                f"Delete student with fingerprint ID {fingerprint_id}? "
                "The device is not connected, so the fingerprint template will remain stored on "
                "the sensor until you connect and delete it separately (ID collisions are possible "
                "if this ID gets reused during enrollment)."
            )
        confirm = QMessageBox.question(self, "Confirm delete", confirm_text)
        if confirm != QMessageBox.Yes:
            return
        try:
            self.service.delete_student(fingerprint_id)
        except PermissionError:
            QMessageBox.warning(
                self,
                "Not allowed",
                "Your current role does not have permission to delete students.",
            )
            return
        if device_connected:
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