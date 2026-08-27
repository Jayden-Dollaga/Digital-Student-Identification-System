#!/usr/bin/env python3
"""
Minimal test to diagnose enrollment issue.
Directly reads from ESP32 after sending ENROLL.
"""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python"))

from core.serial_handler import SerialHandler
from core.commands import cmd_stop, cmd_enroll
from core.logger import log


def minimal_enroll_test():
    print("=" * 70)
    print("MINIMAL ENROLLMENT DIAGNOSTIC")
    print("=" * 70)
    
    # Connect
    print("\n1. Connecting to ESP32...")
    handler = SerialHandler()
    handler.connect()
    time.sleep(0.5)
    
    if not handler.is_connected():
        print("   [FAIL] Could not connect")
        return False
    
    print("   [OK] Connected")
    
    # Send STOP
    print("\n2. Sending STOP command...")
    cmd_stop(handler)
    time.sleep(0.5)
    
    # Clear buffer
    print("\n3. Clearing serial buffer...")
    count = 0
    while True:
        line = handler.read_line()
        if not line:
            break
        count += 1
        print(f"   Cleared: {line[:60]}")
    print(f"   [OK] Cleared {count} buffered lines")
    
    # Send ENROLL
    print("\n4. Sending ENROLL command...")
    result = cmd_enroll(handler)
    print(f"   cmd_enroll() returned: {result}")
    
    if not result:
        print("   [FAIL] cmd_enroll returned False")
        handler.disconnect()
        return False
    
    # Read response for 10 seconds
    print("\n5. Reading ESP32 response for 10 seconds...")
    print("   (Looking for 'ENROLLING FINGER AS ID' message)")
    print()
    
    found_enrolling = False
    start = time.time()
    
    while time.time() - start < 10:
        line = handler.read_line()
        
        if line:
            print(f"   [{time.time()-start:6.2f}s] {line}")
            
            if "ENROLLING FINGER AS ID" in line.upper():
                found_enrolling = True
                print(f"   ✓ FOUND ENROLLMENT START MESSAGE!")
        else:
            # No line available
            time.sleep(0.1)
    
    print()
    print("=" * 70)
    if found_enrolling:
        print("SUCCESS: Found 'ENROLLING FINGER' message from ESP32")
    else:
        print("FAIL: Did NOT receive 'ENROLLING FINGER' message")
        print("\nPossible causes:")
        print("1. ESP32 firmware not running AllInOne version")
        print("2. Serial port/buffer issue")
        print("3. ENROLL command not reaching ESP32")
    print("=" * 70)
    
    handler.disconnect()
    return found_enrolling


if __name__ == "__main__":
    try:
        success = minimal_enroll_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
