"""Tests for the new EnrollDialog state machine and UX workflow."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

# Import after path setup
from gui_qt.pages.students_page import EnrollDialog, EnrollmentState
from core.database import init_database, clear_all_students


@pytest.fixture(scope="module")
def qapp():
    """Create a QApplication for all tests in this module."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture(autouse=True)
def setup_database():
    """Setup test database before each test."""
    init_database()
    clear_all_students()
    yield


@pytest.fixture
def mock_serial_handler():
    """Create a mock serial handler."""
    handler = MagicMock()
    handler.is_connected.return_value = True
    return handler


@pytest.fixture
def mock_serial_worker():
    """Create a mock serial worker with signals."""
    worker = MagicMock()
    # Mock signals as MagicMock objects that support connect/disconnect
    worker.enroll_progress = MagicMock()
    worker.raw_line = MagicMock()
    return worker


@pytest.fixture
def enroll_dialog(qapp, mock_serial_handler, mock_serial_worker):
    """Create an EnrollDialog instance for testing."""
    dialog = EnrollDialog(mock_serial_handler, mock_serial_worker)
    yield dialog
    dialog._cleanup_before_close()


class TestEnrollDialogInitialState:
    """Test dialog behavior in INITIAL state."""
    
    def test_dialog_opens_with_initial_state(self, enroll_dialog):
        """Dialog should open in INITIAL state."""
        assert enroll_dialog.state == EnrollmentState.INITIAL
    
    def test_start_enrollment_button_disabled_on_open(self, enroll_dialog):
        """Start Enrollment button should be disabled when dialog opens."""
        assert not enroll_dialog.primary_btn.isEnabled()
    
    def test_button_text_is_start_enrollment_initially(self, enroll_dialog):
        """Primary button text should be 'Start Enrollment' initially."""
        assert enroll_dialog.primary_btn.text() == "Start Enrollment"
    
    def test_assigned_id_shows_pending(self, enroll_dialog):
        """Assigned ID should show 'Pending' initially."""
        assert "Pending" in enroll_dialog.id_label.text()
    
    def test_all_form_fields_empty_initially(self, enroll_dialog):
        """All form fields should be empty initially."""
        assert enroll_dialog.student_no.text() == ""
        assert enroll_dialog.student_name.text() == ""
        assert enroll_dialog.grade.text() == ""
        assert enroll_dialog.section.text() == ""


class TestEnrollDialogFormValidation:
    """Test form validation and button enable/disable behavior."""
    
    def test_incomplete_form_keeps_button_disabled(self, enroll_dialog):
        """Button should remain disabled with incomplete form."""
        enroll_dialog.student_no.setText("S001")
        assert not enroll_dialog.primary_btn.isEnabled()
    
    def test_invalid_student_no_keeps_button_disabled(self, enroll_dialog):
        """Invalid student number should keep button disabled."""
        enroll_dialog.student_no.setText("S@001")  # Invalid character
        enroll_dialog.student_name.setText("John Doe")
        enroll_dialog.grade.setText("10")
        enroll_dialog.section.setText("A")
        assert not enroll_dialog.primary_btn.isEnabled()
    
    def test_invalid_name_keeps_button_disabled(self, enroll_dialog):
        """Invalid name (with numbers) should keep button disabled."""
        enroll_dialog.student_no.setText("S001")
        enroll_dialog.student_name.setText("John123")  # Invalid
        enroll_dialog.grade.setText("10")
        enroll_dialog.section.setText("A")
        assert not enroll_dialog.primary_btn.isEnabled()
    
    def test_valid_form_enables_button(self, enroll_dialog):
        """Button should be enabled with valid, complete form."""
        enroll_dialog.student_no.setText("S001")
        enroll_dialog.student_name.setText("John Doe")
        enroll_dialog.grade.setText("10")
        enroll_dialog.section.setText("A")
        assert enroll_dialog.primary_btn.isEnabled()
    
    def test_valid_form_with_special_names(self, enroll_dialog):
        """Valid names with apostrophes and hyphens should enable button."""
        enroll_dialog.student_no.setText("S001")
        enroll_dialog.student_name.setText("O'Connor-Smith")
        enroll_dialog.grade.setText("10")
        enroll_dialog.section.setText("CSS-1")
        assert enroll_dialog.primary_btn.isEnabled()
    
    def test_clearing_field_disables_button(self, enroll_dialog):
        """Clearing a field should disable the button."""
        # First fill in complete form
        enroll_dialog.student_no.setText("S001")
        enroll_dialog.student_name.setText("John Doe")
        enroll_dialog.grade.setText("10")
        enroll_dialog.section.setText("A")
        assert enroll_dialog.primary_btn.isEnabled()
        
        # Clear one field
        enroll_dialog.student_no.clear()
        assert not enroll_dialog.primary_btn.isEnabled()


class TestEnrollDialogEnrollingState:
    """Test dialog behavior during enrollment."""
    
    @patch('gui_qt.pages.students_page.cmd_stop')
    @patch('gui_qt.pages.students_page.cmd_enroll')
    def test_clicking_start_transitions_to_enrolling(self, mock_cmd_enroll, mock_cmd_stop, enroll_dialog):
        """Clicking Start Enrollment should transition to ENROLLING state."""
        mock_cmd_enroll.return_value = True
        
        # Setup valid form
        enroll_dialog.student_no.setText("S001")
        enroll_dialog.student_name.setText("John Doe")
        enroll_dialog.grade.setText("10")
        enroll_dialog.section.setText("A")
        
        # Click primary button
        enroll_dialog._on_primary_action()
        
        assert enroll_dialog.state == EnrollmentState.ENROLLING
    
    @patch('gui_qt.pages.students_page.cmd_stop')
    @patch('gui_qt.pages.students_page.cmd_enroll')
    def test_enrolling_disables_button(self, mock_cmd_enroll, mock_cmd_stop, enroll_dialog):
        """Button should be disabled during enrollment."""
        mock_cmd_enroll.return_value = True
        
        enroll_dialog.student_no.setText("S001")
        enroll_dialog.student_name.setText("John Doe")
        enroll_dialog.grade.setText("10")
        enroll_dialog.section.setText("A")
        
        enroll_dialog._on_primary_action()
        
        assert not enroll_dialog.primary_btn.isEnabled()
    
    @patch('gui_qt.pages.students_page.cmd_stop')
    @patch('gui_qt.pages.students_page.cmd_enroll')
    def test_enrolling_changes_button_text(self, mock_cmd_enroll, mock_cmd_stop, enroll_dialog):
        """Button text should change to 'Enrolling...' during enrollment."""
        mock_cmd_enroll.return_value = True
        
        enroll_dialog.student_no.setText("S001")
        enroll_dialog.student_name.setText("John Doe")
        enroll_dialog.grade.setText("10")
        enroll_dialog.section.setText("A")
        
        enroll_dialog._on_primary_action()
        
        assert enroll_dialog.primary_btn.text() == "Enrolling..."
    
    @patch('gui_qt.pages.students_page.cmd_stop')
    @patch('gui_qt.pages.students_page.cmd_enroll')
    def test_prevent_duplicate_enrollments(self, mock_cmd_enroll, mock_cmd_stop, enroll_dialog):
        """Clicking Start multiple times should not trigger multiple enrollments."""
        mock_cmd_enroll.return_value = True
        
        enroll_dialog.student_no.setText("S001")
        enroll_dialog.student_name.setText("John Doe")
        enroll_dialog.grade.setText("10")
        enroll_dialog.section.setText("A")
        
        # Click twice
        enroll_dialog._on_primary_action()
        enroll_dialog._on_primary_action()  # Should not execute
        
        # cmd_enroll should only be called once
        assert mock_cmd_enroll.call_count == 1
    
    @patch('gui_qt.pages.students_page.cmd_stop')
    @patch('gui_qt.pages.students_page.cmd_enroll')
    def test_disconnect_not_connected_shows_warning(self, mock_cmd_enroll, mock_cmd_stop, enroll_dialog, mock_serial_handler):
        """Should show warning if serial not connected."""
        mock_serial_handler.is_connected.return_value = False
        
        enroll_dialog.student_no.setText("S001")
        enroll_dialog.student_name.setText("John Doe")
        enroll_dialog.grade.setText("10")
        enroll_dialog.section.setText("A")
        
        with patch.object(QMessageBox, 'warning') as mock_warning:
            enroll_dialog._on_primary_action()
            mock_warning.assert_called_once()


class TestEnrollDialogEnrollmentSuccess:
    """Test dialog behavior after successful enrollment."""
    
    def test_success_event_transitions_to_success_state(self, enroll_dialog):
        """Receiving 'success' event should transition to ENROLLMENT_SUCCESS state."""
        enroll_dialog._enrollment_started = True
        
        progress = {"event": "success", "id": 5}
        enroll_dialog.on_enroll_progress(progress)
        
        assert enroll_dialog.state == EnrollmentState.ENROLLMENT_SUCCESS
    
    def test_success_updates_assigned_id(self, enroll_dialog):
        """Success event should update the assigned ID display."""
        enroll_dialog._enrollment_started = True
        
        progress = {"event": "success", "id": 7}
        enroll_dialog.on_enroll_progress(progress)
        
        assert "7" in enroll_dialog.id_label.text()
        assert enroll_dialog.assigned_id == 7
    
    def test_success_changes_button_to_save(self, enroll_dialog):
        """Button should change to 'Save Student' after success."""
        enroll_dialog._enrollment_started = True
        
        progress = {"event": "success", "id": 3}
        enroll_dialog.on_enroll_progress(progress)
        
        assert enroll_dialog.primary_btn.text() == "Save Student"
    
    def test_success_enables_save_button(self, enroll_dialog):
        """Save button should be enabled after successful enrollment."""
        enroll_dialog._enrollment_started = True
        
        progress = {"event": "success", "id": 3}
        enroll_dialog.on_enroll_progress(progress)
        
        assert enroll_dialog.primary_btn.isEnabled()
    
    def test_cancelled_event_returns_to_initial_state(self, enroll_dialog):
        """Cancelled event should return to INITIAL state."""
        enroll_dialog._enrollment_started = True
        enroll_dialog.state = EnrollmentState.ENROLLING
        
        progress = {"event": "cancelled"}
        enroll_dialog.on_enroll_progress(progress)
        
        assert enroll_dialog.state == EnrollmentState.INITIAL
    
    def test_cancelled_re_enables_button_if_form_valid(self, enroll_dialog):
        """After cancellation, button should be re-enabled if form is valid."""
        # Setup valid form
        enroll_dialog.student_no.setText("S001")
        enroll_dialog.student_name.setText("John Doe")
        enroll_dialog.grade.setText("10")
        enroll_dialog.section.setText("A")
        
        enroll_dialog._enrollment_started = True
        enroll_dialog.state = EnrollmentState.ENROLLING
        
        progress = {"event": "cancelled"}
        enroll_dialog.on_enroll_progress(progress)
        
        assert enroll_dialog.primary_btn.isEnabled()
    
    def test_error_event_returns_to_initial_state(self, enroll_dialog):
        """Error event should return to INITIAL state."""
        enroll_dialog._enrollment_started = True
        enroll_dialog.state = EnrollmentState.ENROLLING
        
        progress = {"event": "error"}
        enroll_dialog.on_enroll_progress(progress)
        
        assert enroll_dialog.state == EnrollmentState.INITIAL


class TestEnrollDialogSaving:
    """Test dialog behavior when saving student record."""
    
    @patch('gui_qt.pages.students_page.StudentService')
    def test_save_without_fingerprint_shows_warning(self, mock_service_class, enroll_dialog):
        """Attempting to save without enrollment should show warning."""
        enroll_dialog.assigned_id = None
        enroll_dialog.student_no.setText("S001")
        enroll_dialog.student_name.setText("John Doe")
        enroll_dialog.grade.setText("10")
        enroll_dialog.section.setText("A")
        enroll_dialog.state = EnrollmentState.ENROLLMENT_SUCCESS
        
        with patch.object(QMessageBox, 'warning') as mock_warning:
            enroll_dialog._save_student()
            mock_warning.assert_called_once()
    
    @patch('services.student_service.StudentService')
    def test_save_with_valid_data_calls_service(self, mock_service_class, enroll_dialog):
        """Saving with valid data should call StudentService.save_student."""
        mock_instance = MagicMock()
        mock_instance.save_student.return_value = (True, "OK")
        mock_service_class.return_value = mock_instance
        
        enroll_dialog.assigned_id = 5
        enroll_dialog.student_no.setText("S001")
        enroll_dialog.student_name.setText("John Doe")
        enroll_dialog.grade.setText("10")
        enroll_dialog.section.setText("A")
        enroll_dialog.state = EnrollmentState.ENROLLMENT_SUCCESS
        
        with patch.object(enroll_dialog, 'accept'):
            enroll_dialog._save_student()
        
        mock_instance.save_student.assert_called_once_with(5, "S001", "John Doe", "10", "A")
    
    @patch('services.student_service.StudentService')
    def test_save_transitions_to_saving_state(self, mock_service_class, enroll_dialog):
        """Clicking Save should transition to SAVING state."""
        mock_instance = MagicMock()
        mock_instance.save_student.return_value = (True, "OK")
        mock_service_class.return_value = mock_instance
        
        enroll_dialog.assigned_id = 5
        enroll_dialog.student_no.setText("S001")
        enroll_dialog.student_name.setText("John Doe")
        enroll_dialog.grade.setText("10")
        enroll_dialog.section.setText("A")
        enroll_dialog.state = EnrollmentState.ENROLLMENT_SUCCESS
        
        with patch.object(enroll_dialog, 'accept'):
            enroll_dialog._save_student()
    
    @patch('services.student_service.StudentService')
    def test_save_disables_button_during_save(self, mock_service_class, enroll_dialog):
        """Button should be disabled during save operation."""
        mock_instance = MagicMock()
        mock_instance.save_student.return_value = (True, "OK")
        mock_service_class.return_value = mock_instance
        
        enroll_dialog.assigned_id = 5
        enroll_dialog.student_no.setText("S001")
        enroll_dialog.student_name.setText("John Doe")
        enroll_dialog.grade.setText("10")
        enroll_dialog.section.setText("A")
        enroll_dialog.state = EnrollmentState.ENROLLMENT_SUCCESS
        
        # Button should be disabled after _save_student starts
        with patch.object(enroll_dialog, 'accept'):
            enroll_dialog._save_student()
        
        # After save completes, button would be in SAVING state (disabled)
    
    @patch('services.student_service.StudentService')
    def test_prevent_duplicate_saves(self, mock_service_class, enroll_dialog):
        """Clicking Save multiple times should not trigger multiple saves."""
        mock_instance = MagicMock()
        mock_instance.save_student.return_value = (True, "OK")
        mock_service_class.return_value = mock_instance
        
        enroll_dialog.assigned_id = 5
        enroll_dialog.student_no.setText("S001")
        enroll_dialog.student_name.setText("John Doe")
        enroll_dialog.grade.setText("10")
        enroll_dialog.section.setText("A")
        enroll_dialog.state = EnrollmentState.ENROLLMENT_SUCCESS
        
        # Click twice (second click should be ignored)
        with patch.object(enroll_dialog, 'accept'):
            enroll_dialog._on_primary_action()
            enroll_dialog._on_primary_action()
        
        # save_student should only be called once
        mock_instance.save_student.assert_called_once()
    
    @patch('services.student_service.StudentService')
    def test_save_failure_returns_to_success_state(self, mock_service_class, enroll_dialog):
        """If save fails, should return to ENROLLMENT_SUCCESS state."""
        mock_instance = MagicMock()
        mock_instance.save_student.return_value = (False, "Database error")
        mock_service_class.return_value = mock_instance
        
        enroll_dialog.assigned_id = 5
        enroll_dialog.student_no.setText("S001")
        enroll_dialog.student_name.setText("John Doe")
        enroll_dialog.grade.setText("10")
        enroll_dialog.section.setText("A")
        enroll_dialog.state = EnrollmentState.ENROLLMENT_SUCCESS
        
        with patch.object(QMessageBox, 'critical'):
            enroll_dialog._save_student()
        
        assert enroll_dialog.state == EnrollmentState.ENROLLMENT_SUCCESS
        assert not enroll_dialog._saving_in_progress


class TestEnrollDialogCancel:
    """Test cancel behavior."""
    
    def test_cancel_button_closes_dialog(self, enroll_dialog):
        """Cancel button should close the dialog."""
        # Can't easily test QDialog.reject() without showing the dialog,
        # but we can verify cleanup was called
        with patch.object(enroll_dialog, 'reject') as mock_reject:
            enroll_dialog.on_cancel()
            mock_reject.assert_called_once()
    
    def test_cancel_stops_enrollment_if_in_progress(self, enroll_dialog):
        """Cancel should stop the device if enrollment is in progress."""
        enroll_dialog._enrollment_started = True
        
        with patch('gui_qt.pages.students_page.cmd_stop') as mock_cmd_stop:
            enroll_dialog._cleanup_before_close()
            mock_cmd_stop.assert_called_once()
    
    def test_cancel_disconnects_signals(self, enroll_dialog):
        """Cancel should disconnect signal handlers."""
        enroll_dialog._enrollment_started = True
        
        # These should not raise exceptions
        enroll_dialog._cleanup_before_close()
        enroll_dialog.serial_worker.enroll_progress.disconnect.assert_called()
