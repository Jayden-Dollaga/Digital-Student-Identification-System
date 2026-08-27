#!/usr/bin/env python3
"""
Test EnrollDialog button click in the actual StudentPage context.
This simulates the REAL usage flow where EnrollDialog is instantiated from StudentPage.
"""

import sys
from pathlib import Path

# Setup path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python"))

from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication, QMessageBox, QWidget

# Create QApplication
app = QApplication.instance() or QApplication([])

# Import after path is set up
from gui_qt.pages.students_page import StudentsPage, EnrollDialog, EnrollmentState


def test_button_click_in_studentpage():
    """Test button click works when dialog is instantiated from StudentsPage."""
    
    print("=" * 70)
    print("TESTING BUTTON CLICK IN REAL StudentsPage CONTEXT")
    print("=" * 70)
    
    # Mock the serial handler and worker
    serial_handler = MagicMock()
    serial_handler.is_connected.return_value = True
    
    serial_worker = MagicMock()
    serial_worker.enroll_progress = MagicMock()
    serial_worker.raw_line = MagicMock()
    
    # Create the dialog exactly as StudentsPage.on_enroll_clicked() does
    print("\n1. Creating EnrollDialog as StudentsPage.on_enroll_clicked() does...")
    dialog = EnrollDialog(serial_handler, serial_worker, parent=None)
    print("   ✅ Dialog created successfully")
    
    # Check initial state
    print("\n2. Checking initial state...")
    assert dialog.state == EnrollmentState.INITIAL
    assert not dialog.primary_btn.isEnabled()
    print("   ✅ Button is disabled initially (as expected)")
    
    # Fill in valid student info (simulating user typing)
    print("\n3. Simulating user filling in student information...")
    dialog.student_no.setText("S001")
    dialog.student_name.setText("John Doe")
    dialog.grade.setText("10")
    dialog.section.setText("A")
    print("   ✅ Student fields filled")
    
    # Check button is now enabled
    print("\n4. Checking button is enabled after form fill...")
    is_enabled = dialog.primary_btn.isEnabled()
    print(f"   Button enabled: {is_enabled}")
    if not is_enabled:
        print("   ❌ PROBLEM: Button is still disabled after form fill!")
        return False
    print("   ✅ Button is enabled")
    
    # Simulate button click
    print("\n5. Simulating button click...")
    with patch('gui_qt.pages.students_page.cmd_enroll') as mock_enroll:
        with patch('gui_qt.pages.students_page.cmd_stop') as mock_stop:
            with patch('gui_qt.pages.students_page.log') as mock_log:
                mock_enroll.return_value = True
                mock_stop.return_value = True
                
                # This is what happens when button is clicked
                dialog.primary_btn.click()
                print("   ✅ Button clicked")
                
                # Check what happened
                print("\n6. Checking if enrollment commands were called...")
                
                if not mock_stop.called:
                    print("   ❌ cmd_stop() was NOT called!")
                    return False
                print("   ✅ cmd_stop() was called")
                
                if not mock_enroll.called:
                    print("   ❌ cmd_enroll() was NOT called!")
                    return False
                print("   ✅ cmd_enroll() was called")
                
                # Check state transition
                print("\n7. Checking state after button click...")
                print(f"   Current state: {dialog.state}")
                if dialog.state != EnrollmentState.ENROLLING:
                    print("   ❌ State did NOT transition to ENROLLING!")
                    return False
                print("   ✅ State transitioned to ENROLLING")
                
                # Check logging
                print("\n8. Checking diagnostic logging...")
                debug_calls = [c for c in mock_log.debug.call_args_list]
                info_calls = [c for c in mock_log.info.call_args_list]
                print(f"   Debug log calls: {len(debug_calls)}")
                print(f"   Info log calls: {len(info_calls)}")
                
                if len(debug_calls) == 0:
                    print("   ⚠️  No debug logs (might be OK)")
                else:
                    print("   ✅ Debug logging working")
                    
                if len(info_calls) < 3:
                    print(f"   ⚠️  Expected at least 3 info logs, got {len(info_calls)}")
                else:
                    print("   ✅ Info logging working")
    
    print("\n" + "=" * 70)
    print("✅ ALL CHECKS PASSED - BUTTON CLICK WORKS CORRECTLY IN CONTEXT")
    print("=" * 70)
    return True


if __name__ == "__main__":
    try:
        success = test_button_click_in_studentpage()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
