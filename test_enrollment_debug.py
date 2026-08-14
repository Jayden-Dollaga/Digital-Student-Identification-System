#!/usr/bin/env python3
"""
Direct test of enrollment flow to diagnose regression.
Run this to see if cmd_enroll is working correctly with a real SerialHandler.
"""

import sys
import time
from pathlib import Path

# Setup path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python"))

from core.serial_handler import SerialHandler
from core.commands import cmd_enroll, cmd_stop, cmd_list
from core.logger import log

def test_enrollment_flow():
    """Test if cmd_enroll works with the real SerialHandler."""
    
    print("=" * 60)
    print("ENROLLMENT FLOW DIAGNOSTIC TEST")
    print("=" * 60)
    
    # Initialize serial handler
    print("\n1. Initializing SerialHandler...")
    handler = SerialHandler()
    
    # Try to connect
    print("2. Attempting connection...")
    handler.connect()
    time.sleep(1)
    
    is_connected = handler.is_connected()
    print(f"   Connected: {is_connected}")
    
    if not is_connected:
        print("\n[FAIL] DIAGNOSTIC: SerialHandler not connected")
        print("   Cannot test cmd_enroll without connection")
        return False
    
    print("\n[OK] Serial connection successful")
    
    # Check current fingerprint count
    print("\n3. Querying current fingerprint count...")
    try:
        cmd_list(handler)
        time.sleep(0.5)
    except Exception as e:
        print(f"   cmd_list error: {e}")
    
    # Test cmd_stop (cleanup any previous state)
    print("\n4. Sending STOP command...")
    stop_result = cmd_stop(handler)
    print(f"   cmd_stop() returned: {stop_result}")
    time.sleep(1)
    
    # Test cmd_enroll
    print("\n5. Sending ENROLL command...")
    try:
        enroll_result = cmd_enroll(handler)
        print(f"   cmd_enroll() returned: {enroll_result}")
        
        if enroll_result:
            print("   [OK] ENROLL command sent successfully")
            print("   Waiting for ESP32 response...")
            
            # Wait for enrollment prompts from ESP32
            for i in range(10):
                time.sleep(0.5)
                print(f"   Waiting... ({i+1}/10)")
            
            print("\n   📋 Check ESP32 serial output for:")
            print("      - 'ENROLLING FINGER AS ID #X'")
            print("      - 'STEP 1: Place finger on sensor'")
            print("      - 'STEP 2: Remove finger'")
            print("      - 'STEP 3: Place same finger again'")
            
        else:
            print("   [FAIL] cmd_enroll() returned False")
            print("   DIAGNOSTIC: Serial communication failed")
            return False
            
    except Exception as e:
        print(f"   [ERROR] Exception in cmd_enroll: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        print("\n6. Cleaning up...")
        try:
            cmd_stop(handler)
        except:
            pass
        handler.disconnect()
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = test_enrollment_flow()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
