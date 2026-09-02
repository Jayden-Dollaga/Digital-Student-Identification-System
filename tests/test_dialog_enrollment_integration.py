#!/usr/bin/env python3
"""
Full integration test simulating the exact GUI enrollment flow.
Creates a real EnrollDialog, shows it, and verifies enrollment signal.

This is a hardware-in-the-loop test: it needs an actual ESP32 plugged in
to mean anything, and serial_handler.connect() does real port discovery
with no hard upper bound on how long that can take in every failure mode.
Under pytest (no hardware, running alongside other Qt tests) that used to
either crash on a duplicate QApplication or hang indefinitely - neither of
which is an acceptable outcome for an automated suite. It now skips
cleanly and fast unless a real serial port is actually present AND
DSIS_RUN_HARDWARE_TESTS=1 is set, so a normal `pytest` run never touches
hardware-dependent code at all.

To actually run this against real hardware:
    DSIS_RUN_HARDWARE_TESTS=1 python -m pytest tests/test_dialog_enrollment_integration.py -v -s
or simply:
    python tests/test_dialog_enrollment_integration.py
"""

import os
import sys
import time
from pathlib import Path

import pytest

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


def _any_serial_port_present() -> bool:
    """Cheap, non-blocking check - just enumerates what the OS already
    knows about, never opens a port. Not proof an ESP32 is attached (could
    be some other serial device, or a stale entry), but a fast, safe way
    to rule out the common case of "nothing plugged in at all" before
    considering the slower, blocking discovery path."""
    try:
        from serial.tools import list_ports
        return len(list(list_ports.comports())) > 0
    except Exception:
        return False


def _skip_or_fail(reason: str) -> bool:
    """pytest.skip() when actually running under pytest (so it's reported
    as skipped, not passed or failed); a clean printed message + False
    return when run as a standalone script instead, since pytest.skip()
    raises an exception type that a plain script isn't set up to catch."""
    if "PYTEST_CURRENT_TEST" in os.environ:
        pytest.skip(reason)
    print(f"   [SKIP] {reason}")
    return False


@pytest.mark.skipif(
    os.environ.get("DSIS_RUN_HARDWARE_TESTS") != "1",
    reason=(
        "Hardware-in-the-loop test - needs a real ESP32 and explicit opt-in. "
        "Run with DSIS_RUN_HARDWARE_TESTS=1 to include it."
    ),
)
def test_enrollment_dialog_in_gui():
    """Test enrollment with real dialog and Qt event loop."""

    if not _any_serial_port_present():
        return _skip_or_fail("No serial ports detected on this machine - nothing to test against.")

    print("=" * 70)
    print("FULL GUI ENROLLMENT INTEGRATION TEST")
    print("=" * 70)

    app = QApplication.instance() or QApplication(sys.argv)
    
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
        return _skip_or_fail("A serial port was detected but no ESP32 responded - nothing to test against.")
    
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
