#!/usr/bin/env python3
"""
Full integration test simulating the exact GUI enrollment flow.
Creates a real EnrollDialog, shows it, and verifies enrollment signal.
"""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QTimer

from core.serial_handler import SerialHandler
from core.commands import cmd_enroll, cmd_stop
from core.attendance import AttendanceProcessor
from gui_qt.workers.serial_worker import SerialWorker
from gui_qt.pages.students_page import EnrollDialog
from core.logger import log


def test_enrollment_dialog_in_gui():
    """Test enrollment with real dialog and Qt event loop."""
    
    print("=" * 70)
    print("FULL GUI ENROLLMENT INTEGRATION TEST")
    print("=" * 70)
    
    app = QApplication(sys.argv)
    
    # Create main window just to have something to parent to
    main_window = QMainWindow()
    main_window.setWindowTitle("Enrollment Test")
    
    # Setup serial
    print("\n1. Setting up serial communication...")
    serial_handler = SerialHandler()
    serial_handler.connect()
    time.sleep(0.5)
    
    if not serial_handler.is_connected():
        print("   [FAIL] Not connected")
        return False
    
    print("   [OK] Connected")
    
    # Setup SerialWorker
    print("\n2. Starting SerialWorker...")
    attendance_processor = AttendanceProcessor(serial_handler)
    serial_worker = SerialWorker(serial_handler, attendance_processor)
    serial_worker.start()
    time.sleep(0.5)
    print("   [OK] Started")
    
    # Create dialog
    print("\n3. Creating EnrollDialog...")
    dialog = EnrollDialog(serial_handler, serial_worker, parent=main_window)
    print("   [OK] Dialog created")
    
    # Track signals
    print("\n4. Monitoring for enrollment signals...")
    received_signals = []
    
    def track_enroll_progress(progress):
        event = progress.get("event")
        id_val = progress.get("id")
        print(f"   [SIGNAL] Enrollment event: {event} (ID={id_val})")
        received_signals.append(event)
        dialog.on_enroll_progress(progress)
    
    # Connect tracking function
    dialog.serial_worker.enroll_progress.disconnect(dialog.on_enroll_progress)
    dialog.serial_worker.enroll_progress.connect(track_enroll_progress)
    
    # Setup auto-send of enrollment command after dialog opens
    print("\n5. Setting up auto-enrollment in 1 second...")
    
    def auto_enroll():
        print("   Sending STOP...")
        cmd_stop(serial_handler)
        time.sleep(0.3)
        print("   Sending ENROLL...")
        result = cmd_enroll(serial_handler)
        print(f"   cmd_enroll() returned: {result}")
    
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(auto_enroll)
    timer.start(1000)
    
    # Show dialog and process events
    print("\n6. Showing dialog and processing events...")
    print("   (Will wait for enrollment signal for 10 seconds)")
    
    start_time = time.time()
    while time.time() - start_time < 10:
        app.processEvents()
        if "enrolling" in received_signals:
            print(f"   [OK] Received enrolling signal at {time.time()-start_time:.1f}s!")
            break
        time.sleep(0.05)
    
    # Cleanup
    print("\n7. Cleaning up...")
    dialog.close()
    serial_worker.quit()
    serial_worker.wait()
    serial_handler.disconnect()
    
    print()
    print("=" * 70)
    if "enrolling" in received_signals:
        print("SUCCESS: Dialog received enrollment signal from SerialWorker")
        print(f"Received signals: {received_signals}")
    else:
        print("FAIL: Dialog did NOT receive enrollment signal")
        print(f"Received signals: {received_signals if received_signals else 'NONE'}")
    print("=" * 70)
    
    return "enrolling" in received_signals


if __name__ == "__main__":
    try:
        success = test_enrollment_dialog_in_gui()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
