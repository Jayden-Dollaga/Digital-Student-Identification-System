# Troubleshooting Guide - Digital Student Identification System (DSIS)

## Issue: "PermissionError(13): Access is denied" on COM Port

### Root Cause
The fingerprint device on **COM4** is being blocked by Windows or another application. This is an **OS-level port access issue**, not a software bug.

### Symptoms
```
PermissionError(13, 'Access is denied.'): Port in use by another application or USB driver issue
```

Logs show the app successfully:
- ✅ Enumerates available ports (COM4, COM9, COM1)
- ✅ Identifies COM4 as the fingerprint device
- ✅ Attempts handshake on correct port
- ❌ Fails with PermissionError when trying to open COM4

### Resolution Steps (Try in Order)

#### 1. **Close Conflicting Applications**
Check for any of these running and close them:
- Arduino IDE
- Serial Monitor applications
- PuTTY, TeraTerm, or other serial terminals
- Python scripts using `python -c "import serial; s=serial.Serial('COM4')"`
- Other DSIS instances

**Windows Task Manager Check:**
```
Ctrl + Shift + Esc → Processes tab → Search for: arduino, serial, putty, python
```

#### 2. **Unplug and Replug the USB Device**
- Unplug the ESP32 fingerprint device from USB
- Wait 3 seconds
- Plug it back in
- Wait for Windows to reinstall the driver (~2 seconds)
- Try connecting again

#### 3. **Check Device Manager**
1. Press `Win + X` → Device Manager
2. Look for "Ports (COM & LPT)" section
3. Find the device with a **⚠ Yellow Warning Triangle** (if any)
   - Right-click → Update driver → Search automatically
4. Check for **Silicon Labs CP210x USB to UART Bridge**
   - Should be `COM4` with no warnings
5. If you see `COM4` listed multiple times, **uninstall all instances** and replug

#### 4. **Verify Port is Not Held by Another Service**
Run PowerShell as Administrator:
```powershell
# List all processes using COM ports
Get-Process | Where-Object { $_.Handles -gt 100 } | ForEach-Object {
    try {
        if ((Get-WmiObject -Query "SELECT * FROM Win32_SerialPort WHERE DeviceID='COM4'" -ErrorAction SilentlyContinue)) {
            "Process: $($_.Name) (PID: $($_.Id))"
        }
    } catch { }
}
```

#### 5. **Update USB Driver**
Visit Silicon Labs website:
- Download: CP210x USB to UART Bridge VCP Drivers
- https://www.silabs.com/products/development-tools/software/usb-to-uart-bridge-vcp-drivers
- Install for Windows
- Restart computer
- Replug device

#### 6. **Try Different USB Port**
- Plug the ESP32 into a different USB port on your computer
- Windows will re-enumerate and may assign a different COM port
- Note the new port number and update settings if needed

#### 7. **Check for Driver Conflicts**
1. Device Manager → View → Show hidden devices
2. Look in "Other devices" for unknown items
3. If you see a device with name like "COM Port" or similar:
   - Right-click → Delete
   - Replug device to force re-detection

### Advanced Diagnostics

#### View All COM Ports and Their Status
```powershell
# Run in PowerShell (Admin)
[System.IO.Ports.SerialPort]::GetPortNames()
# Or: 
Get-WmiObject Win32_SerialPort | Select-Object Name, Description, DeviceID
```

#### Test COM Port Directly (Python)
```python
import serial
import time

for port in ['COM4', 'COM8', 'COM9']:
    try:
        print(f"Testing {port}...")
        s = serial.Serial(port, 115200, timeout=1)
        s.write(b"ID?\n")
        response = s.readline(timeout=2)
        print(f"  ✓ {port} opened successfully: {response}")
        s.close()
    except PermissionError as e:
        print(f"  ✗ {port} BLOCKED: {e}")
    except Exception as e:
        print(f"  ? {port} Error: {e}")
```

### Software Improvements Made

The application now includes several improvements for better diagnostics:

#### 1. **Enhanced Error Reporting**
- Shows **all** access denied errors, not just the last error
- Clearly highlights which ports are blocked (likely the real device)
- Example: `"Access denied on 1 ports (likely real devices); first: COM4: PermissionError..."`

#### 2. **Stale Port Cleanup**
- Stored COM port (COM8) is automatically validated
- If port no longer exists, app logs this and skips reconnect attempts to that port
- Reduces log spam from retrying non-existent ports

#### 3. **Smarter Reconnect Logic**
- Auto-detect mode: Refreshes port enumeration on each retry (detects newly plugged devices)
- Explicit port mode: Validates port still exists after 2 attempts
- After 3+ failed attempts, suggests switching to auto-detect
- Exponential backoff: Waits 2s, 4s, 8s, 16s, 30s (capped)

#### 4. **Connection Diagnostics**
Main window shows:
- Which ports were probed
- Why each port failed (access denied vs. no handshake vs. no device)
- Suggestions for resolution

### Workflow Recommendations

#### Best Practice: Auto-Detect
1. Click **Connect** without specifying a port
2. App probes all available ports
3. Device found automatically
4. Future connections use discovered port as preferred

#### For Specific Port: Explicit Mode
1. Click **Settings** → Manual COM Port
2. Enter exact port (e.g., COM4)
3. Click Connect
4. Fails if port blocked or has no device

#### During Development: Keep Device Plugged
- Don't unplug device while app is running
- Each USB reconnect requires re-enumeration
- If you must unplug:
  1. Close app or click Disconnect
  2. Unplug device
  3. Replug device
  4. Wait 3 seconds for driver to load
  5. Open app and Connect

### When to Contact Support

If you've tried all steps above and still see **PermissionError(13)**:

1. Run this diagnostic:
```powershell
# Generate diagnostics file
cd "c:\Users\EnforcerX\Downloads\Arduino-IDE - Project\AI-Assisted Fingerprint Attendance System"
python -c "
from python.core.device_discovery import list_serial_ports, discover_device
ports = list_serial_ports()
print('Available ports:', ports)
for port in ports:
    success, meta, error = discover_device(preferred_port=port, allow_search=False)
    print(f'{port}: {\"OK\" if success else error}')
" > diagnostics.txt 2>&1
```

2. Share:
   - `data/logs/fingerprint_attendance.log` (last 100 lines)
   - `diagnostics.txt` output
   - Device Manager screenshot (Ports section)
   - Windows version (Win + R → winver)

### Related Issues

- **No ports enumerated**: Check if pyserial is installed (`pip install pyserial`)
- **Connects but then disconnects**: See [RECONNECT_HANDLING.md](./docs/RECONNECT_HANDLING.md)
- **Wrong port selected**: Settings are stored in `data/settings.json` — delete to reset
- **Multiple COM8 entries in Device Manager**: See section "Check for Driver Conflicts" above
