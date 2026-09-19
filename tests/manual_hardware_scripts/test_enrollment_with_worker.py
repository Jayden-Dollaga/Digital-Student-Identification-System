#!/usr/bin/env python3
"""
Simulate the EXACT enrollment flow that happens in the Qt GUI.
This helps identify if the problem is in the dialog code or elsewhere.
"""

import sys
import time
import threading
from pathlib import Path

# Setup path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python"))

# CRITICAL: Create QApplication before using Qt signals. Guarded because
# this file has no test_-prefixed function (pytest won't ever call
# simulate_enrollment_with_worker() automatically), but pytest still
# imports every test_*.py file during collection - so an unconditional
# QApplication(sys.argv) here crashed collection for the *whole suite*
# whenever another Qt test's QApplication already existed, even though
# this file was never going to run anything itself.
from PySide6.QtWidgets import QApplication
app = QApplication.instance() or QApplication(sys.argv)

from core.serial_handler import SerialHandler
from core.commands import cmd_enroll, cmd_stop
from core.attendance import AttendanceProcessor
from gui_qt.workers.serial_worker import SerialWorker
from core.logger import log


def simulate_enrollment_with_worker():
    """Simulate the exact enrollment flow with SerialWorker running."""
    
    print("=" * 70)
    print("SIMULATING ENROLLMENT FLOW WITH SERIALWORKER")
    print("=" * 70)
    
    # Setup
    print("\n1. Initializing SerialHandler and Attendance Processor...")
    serial_handler = SerialHandler()
    attendance_processor = AttendanceProcessor(serial_handler)
    
    # Connect
    print("2. Connecting to ESP32...")
    serial_handler.connect()
    time.sleep(1)
    
    if not serial_handler.is_connected():
        print("   [FAIL] Not connected to ESP32")
        return False
    
    print("   [OK] Connected to ESP32")
    
    # Start SerialWorker
    print("\n3. Starting SerialWorker (this reads from serial port)...")
    serial_worker = SerialWorker(serial_handler, attendance_processor)
    serial_worker.start()
    time.sleep(1)
    print("   [OK] SerialWorker started")
    
    # Track received progress events
    received_events = []
    
    def track_progress(progress):
        event = progress.get("event")
        id_val = progress.get("id")
        print(f"   [SIGNAL] Received enroll_progress: event={event}, id={id_val}")
        received_events.append(event)
    
    # Connect the signal
    print("\n4. Connecting to enroll_progress signal...")
    serial_worker.enroll_progress.connect(track_progress)
    print("   [OK] Signal connected")
    
    # Send enrollment commands (like _start_enrollment does)
    print("\n5. Sending enrollment commands...")
    print("   - Sending STOP...")
    cmd_stop(serial_handler)
    time.sleep(0.5)
    
    print("   - Sending ENROLL...")
    enroll_result = cmd_enroll(serial_handler)
    print(f"   [RESULT] cmd_enroll() returned: {enroll_result}")
    
    if not enroll_result:
        print("   [FAIL] cmd_enroll returned False")
        serial_worker.quit()
        serial_worker.wait()
        serial_handler.disconnect()
        return False
    
    print("\n6. Waiting for ESP32 response via SerialWorker...")
    print("   (This simulates the dialog waiting for enrollment events)")
    
    # Wait for enrollment to complete or timeout
    for i in range(30):  # Wait up to 15 seconds
        time.sleep(0.5)
        # Process Qt events to allow signals to be delivered
        QApplication.processEvents()
        if "success" in received_events:
            print(f"\n   [OK] Enrollment successful after {i*0.5:.1f} seconds")
            break
        if "error" in received_events:
            print(f"\n   [FAIL] Enrollment error after {i*0.5:.1f} seconds")
            break
        if "enrolling" in received_events:
            # Received enrolling event, keep waiting for success
            if i % 4 == 0:  # Print every 2 seconds
                print(f"   Enrolled, waiting for success... ({i+1}/30, {i*0.5:.1f} seconds elapsed)")
        else:
            print(f"   Waiting... ({i+1}/30, {i*0.5:.1f} seconds elapsed)")
    else:
        print("\n   [TIMEOUT] No response after 15 seconds")
    
    # Report what was received
    print(f"\n7. Summary of events received:")
    if not received_events:
        print("   [FAIL] NO EVENTS RECEIVED")
        print("   This means SerialWorker is not parsing enrollment messages")
    else:
        print(f"   [OK] Received {len(received_events)} event(s):")
        for event in received_events:
            print(f"      - {event}")
    
    # Cleanup
    print("\n8. Cleaning up...")
    cmd_stop(serial_handler)
    serial_worker.quit()
    serial_worker.wait()
    serial_handler.disconnect()
    print("   [OK] Cleaned up")
    
    print("\n" + "=" * 70)
    if received_events:
        print("SUCCESS: Enrollment flow works correctly with SerialWorker")
    else:
        print("PROBLEM: SerialWorker is not receiving/parsing enrollment events")
    print("=" * 70)
    
    return bool(received_events)


if __name__ == "__main__":
    try:
        success = simulate_enrollment_with_worker()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
