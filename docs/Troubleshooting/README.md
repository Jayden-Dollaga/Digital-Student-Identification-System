# DSIS Troubleshooting

## Connection failure

1. Close Arduino Serial Monitor and all other serial terminals.
2. Confirm the board appears under **Device Manager > Ports (COM & LPT)**.
3. Confirm the USB driver matches the board's USB interface chip.
4. Click the ESP32 **EN/RESET** button.
5. If it still does not connect, unplug the USB cable, wait 5-10 seconds, plug it back in, and wait for Windows to recreate the COM port.
6. Use **Forget saved port** if the saved COM number is stale.
7. Retry only after DSIS shows device metadata and fingerprint count.
8. If it still fails, inspect the latest timestamped file under `data/logs/` for serial, handshake, permission, or driver errors.

A successful connection requires a valid DSIS identity response at 115200 baud. The internal ESP32-to-AS608 UART uses 57600 baud and is not a desktop setting.

## No COM port

Use a data-capable USB cable and identify the USB bridge in Device Manager. Install the matching CP210x, CH340/CH341, CH9102, FTDI, or board-specific native USB driver. Python package installation does not install Windows USB drivers.

## Access denied

A serial terminal or another DSIS process may own the port. Close Arduino IDE, serial monitors, terminal tools, and duplicate DSIS windows. If the port remains locked after reconnecting the board, restart Windows or use a trusted handle-inspection utility.

## Sensor does not respond

Verify the maintained firmware, crossed wiring, and power:

- AS608 TX -> ESP32 GPIO14
- AS608 RX -> ESP32 GPIO27
- GND -> GND
- V+ -> the voltage required by the exact AS608 module revision

Do not use the placeholder `firmware/prebuilt/attendance_v1.0.bin` or historical standalone sketches as substitutes for the all-in-one firmware.

## Enrollment, delete, or wipe problems

- Stop scan mode before starting another device operation.
- Enrollment saves the student only after the device reports success.
- Delete removes the local profile only after a connected device confirms fingerprint deletion.
- Device wipe and local database clearing are separate operations.
- Reconnect after a disconnect and refresh the device fingerprint count before retrying.

## Logs and diagnostics

Logs use timestamped files under `data/logs/`. Include the latest file, Device Manager device name, COM port, USB bridge family, board type, and firmware version when reporting a problem.

From the repository root, list detected serial ports with:

`python -c "from python.core.device_discovery import list_serial_ports; print(list_serial_ports())"`

## Validation commands

```powershell
node --check python/gui_web/web/app.js
python -m pytest -q tests/test_gui_web_smoke.py tests/test_permissions_and_attendance_tagging.py tests/test_database_security.py
```

A physical ESP32 and AS608 are required for hardware behavior. Prototype and archived Qt tests do not replace hardware validation.

For the legacy detailed guide, see [the existing troubleshooting document](../TROUBLESHOOTING.md).

Last reviewed: 2026-09-11, against commit `aa457e0`.
