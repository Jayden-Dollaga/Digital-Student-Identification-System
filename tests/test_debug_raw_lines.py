#!/usr/bin/env python3
"""
Debug what raw lines SerialWorker is receiving from ESP32.
"""

import sys
import time
from pathlib import Path

# Setup path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python"))

from core.serial_handler import SerialHandler
from core.commands import cmd_enroll, cmd_stop
from core.attendance import AttendanceProcessor
from gui_qt.workers.serial_worker import SerialWorker


def debug_raw_lines():
    """Monitor raw lines received from ESP32."""
    
    print("=" * 70)
    print("DEBUGGING RAW LINES FROM ESP32")
    print("=" * 70)
    
    # Setup
    serial_handler = SerialHandler()
    attendance_processor = AttendanceProcessor(serial_handler)
    
    # Connect
    print("\n1. Connecting to ESP32...")
    serial_handler.connect()
    time.sleep(1)
    
    if not serial_handler.is_connected():
        print("   [FAIL] Not connected")
        return False
    
    print("   [OK] Connected")
    
    # Start SerialWorker
    print("\n2. Starting SerialWorker...")
    serial_worker = SerialWorker(serial_handler, attendance_processor)
    
    # Track all lines
    all_lines = []
    enrollment_lines = []
    
    def track_raw_line(line):
        all_lines.append(line)
        if any(keyword in line.upper() for keyword in ["ENROLL", "FINGER", "STEP", "SUCCESS", "ERROR"]):
            enrollment_lines.append(line)
            print(f"   [ENROLLMENT] {line}")
    
    serial_worker.raw_line.connect(track_raw_line)
    serial_worker.start()
    time.sleep(1)
    
    # Send commands
    print("\n3. Sending STOP and ENROLL...")
    cmd_stop(serial_handler)
    time.sleep(0.5)
    cmd_enroll(serial_handler)
    
    # Wait and collect data
    print("\n4. Collecting raw output for 15 seconds...")
    for i in range(30):
        time.sleep(0.5)
        if (i % 2) == 0:
            print(f"   [{i//2 * 5} seconds] Received {len(all_lines)} lines, {len(enrollment_lines)} enrollment-related")
    
    # Report findings
    print(f"\n5. Analysis:")
    print(f"   Total lines received: {len(all_lines)}")
    print(f"   Enrollment-related lines: {len(enrollment_lines)}")
    
    if enrollment_lines:
        print("\n   Sample enrollment lines:")
        for line in enrollment_lines[:10]:
            print(f"      [{line}]")
    else:
        print("\n   No enrollment-related lines received!")
        if all_lines:
            print("\n   Sample of all received lines:")
            for line in all_lines[:10]:
                print(f"      [{line}]")
        else:
            print("\n   NO LINES RECEIVED AT ALL!")
    
    # Cleanup
    cmd_stop(serial_handler)
    serial_worker.quit()
    serial_worker.wait()
    serial_handler.disconnect()
    
    print("\n" + "=" * 70)
    return bool(enrollment_lines)


if __name__ == "__main__":
    try:
        success = debug_raw_lines()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInterrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
