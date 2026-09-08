# Troubleshooting DSIS

## No COM Port Appears

1. Connect the ESP32 with a data-capable USB cable.
2. Open **Device Manager > Ports (COM & LPT)**.
3. Install the driver matching the USB bridge shown there. CP210x, CH340/CH341, CH9102, and FTDI boards use different drivers. See the [USB Serial Drivers section](UserGuide/installation-guide.md#41-usb-serial-driver).
4. Try another USB port and reconnect the board.

Python packages do not install Windows USB drivers. Native-USB ESP32 boards may expose USB CDC or USB-JTAG instead of a COM port; those variants are not verified by this project.

## Access Denied on a COM Port

The selected COM port is already open in another application. COM numbers such as COM4 are examples and vary by computer.

Close Arduino IDE, Arduino Serial Monitor, PuTTY, Tera Term, other serial terminals, other DSIS instances, and Python processes that may use the port. Disconnect and reconnect the board, then try again. Windows does not provide a dependable built-in mapping from an open COM handle to its owning process; use a trusted handle-inspection utility if the port remains locked.

## Firmware Upload Fails

- Select **ESP32 Arduino > ESP32 Dev Module** for the verified ESP32 WROOM-32 target.
- Select the COM port currently assigned to the board.
- Use an upload speed of **115200**.
- Try a different data cable or USB port.
- Press and hold the board's **BOOT** button while upload begins if the board does not enter download mode.

Upload the maintained [all-in-one firmware](../firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino). The historical sketches and `firmware/prebuilt/attendance_v1.0.bin` placeholder are not interchangeable with the desktop application.

## App Connects but Sensor Does Not Respond

Check the sensor power and crossed UART wiring:

- AS608 TX to ESP32 GPIO14 (UART2 RX)
- AS608 RX to ESP32 GPIO27 (UART2 TX)
- GND to GND
- V+ connected according to the exact sensor module revision

The PC-to-ESP32 connection uses **115200 baud**. The internal ESP32-to-AS608 connection uses **57600 baud** and is configured by the firmware, not in the desktop app.

## Test the Host Serial Connection

Run this from the project root after closing the DSIS application and all serial monitors:

```python
import serial

port = "COM5"  # Replace with the port shown by Device Manager.
try:
    with serial.Serial(port, 115200, timeout=2) as connection:
        connection.write(b"ID?\n")
        print(connection.readline())
except PermissionError as error:
    print(f"Port is already in use: {error}")
except Exception as error:
    print(f"Serial test failed: {error}")
```

The application can auto-discover a device when Windows exposes a COM port and the firmware responds to the DSIS identity handshake. In the Qt app, click **Connect** and use auto-discovery or select the detected port manually.

## Collect Diagnostics

From the project root, run:

```powershell
python -c "from python.core.device_discovery import list_serial_ports; print(list_serial_ports())"
```

When reporting a problem, include the output, the Device Manager device name, the selected board, the USB bridge family, and the relevant lines from `data/logs/fingerprint_attendance.log`.

## V3 Operation State Problems

V3 keeps the serial reader active for the entire connection. If the board is
unplugged during enrollment, delete, or wipe, the pending operation is cleared
and the UI returns to disconnected state. Reconnect the board and refresh the
fingerprint count before retrying.

If the UI reports a timeout:

1. Close Arduino Serial Monitor and any other serial terminal.
2. Confirm the firmware responds to `ID?` at 115200 baud.
3. Disconnect and reconnect the board.
4. Retry the operation only after the device metadata and fingerprint count appear.

## V3 Role Restrictions

Administrator can use all workflows. Teacher can scan, export, and create
backups. Guest can scan only. These restrictions are enforced in the Python
bridge as well as by the visible controls, so changing the page or calling a
bridge method directly does not bypass them.

## Automated and Hardware Verification

Run the software-only checks from the project root:

```powershell
python -m pytest -q
python -m py_compile python/gui_web/api.py
node --check python/gui_web/web/app.js
```

These checks cover mocked lifecycle transitions and the V3 web shell. A real
ESP32 is still required to verify sensor prompts, physical fingerprint
matching, enrollment capture, device deletion, and wipe behavior.

The opt-in safe hardware smoke test is:

```powershell
$env:DSIS_RUN_HARDWARE = "1"
$env:PYTHONPATH = "$PWD\python"
python -m pytest -q tests/physical_esp32_smoke.py
```

On 2026-09-09 it passed against COM4, identifying the DSIS ESP32/AS608 device
with firmware 1.0 and protocol 1. It verified auto-discovery, connection,
fingerprint-count traffic, scan mode entry/exit, enrollment cancellation, and
disconnect. The test deliberately does not delete valid fingerprints or wipe
the sensor; perform those two destructive checks only with an approved test
record and a backup.

### Physical delete result and firmware fix

The empty COM4 test device was wiped successfully. Before the firmware update,
`DELETE:1` incorrectly returned `SUCCESS - ID #1 deleted` even though the device
reported zero stored fingerprints. The maintained firmware now calls
`loadModel()` before `deleteModel()` so an absent template reports failure
instead of false success. Upload
`firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino` through
Arduino IDE or the bundled Arduino CLI, then rerun the guarded hardware test
before accepting delete verification. This was completed on 2026-09-09 using
the bundled Arduino CLI 1.5.1, ESP32 core 3.3.11, and Adafruit Fingerprint
Sensor Library 2.1.4. The firmware upload was hash-verified on COM4, and the
guarded physical test passed both empty-device wipe and absent-ID delete.

The opt-in Qt enrollment integration test also passed on COM4 on 2026-09-09:
the real dialog received the device's `enrolling` event for ID 1, then the
serial worker stopped and the device disconnected cleanly. No finger was
placed and no template was saved.

If VS Code reports missing `Arduino.h` or `Adafruit_Fingerprint.h`, reload the
workspace after checking `.vscode/c_cpp_properties.json`. It points IntelliSense
at the installed ESP32 3.3.11 core, Xtensa compiler, and Adafruit library; the
Arduino CLI build remains the authoritative firmware compile check.
