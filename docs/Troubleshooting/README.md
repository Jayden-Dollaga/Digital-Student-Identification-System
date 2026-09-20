# DSIS Troubleshooting Guide

This guide covers the maintained DSIS v3 application and the documented ESP32/AS608 hardware target.

## Quick diagnosis

| Symptom | First checks |
| --- | --- |
| No COM port | USB cable, Windows driver, Device Manager |
| Access denied | Close Serial Monitor/serial tools/other DSIS instances |
| Device rejected | Correct all-in-one firmware, ID handshake, protocol |
| Sensor not responding | AS608 wiring, power, GPIO14/GPIO27, sensor UART |
| Weak match | Review application min_confidence setting |
| Enrollment failure | Same finger twice, sensor surface, connection |
| Repeated attendance | Firmware delay + application cooldown |
| Restore failure | Backup file type/path/permission |
| Wipe issue | Back up first; verify hardware and local-data phases |

## 1. No COM port appears

1. Use a data-capable USB cable.
2. Open **Device Manager → Ports (COM & LPT)**.
3. Identify the board's USB interface.
4. Install the matching driver.
5. Try another USB port or cable.

Common bridge families are CP210x, CH340/CH341, CH9102, and FTDI. Some native-USB ESP32 variants use USB CDC or USB-JTAG; those are not the project's verified hardware target.

Python package installation does not install Windows USB drivers.

## 2. Access denied / port already in use

Close Arduino Serial Monitor/Plotter, serial-terminal applications, other DSIS instances, and scripts that opened the COM port with pyserial.

Reconnect the board after closing the conflicting application.

## 3. Saved COM port is stale

Windows can assign a new COM number after the ESP32 is moved. Use **Forget saved port**, leave auto-detection enabled, and connect again.

The serial handler can also detect a saved port that is no longer present and fall back to discovery.

## 4. Device is found but rejected

DSIS validates the selected device instead of accepting every COM port.

The discovery layer sends `ID?` and expects DSIS identity metadata and a supported protocol version.

| Field | Expected |
| --- | --- |
| Device | Digital Student Identification System |
| Board | ESP32 |
| Sensor | AS608 |
| Protocol | 1 |

If another firmware sketch is installed, its response may not satisfy the DSIS handshake.

## 5. Sensor does not respond

Check the maintained wiring:

```text
AS608 TX → ESP32 GPIO14
AS608 RX → ESP32 GPIO27
AS608 GND → ESP32 GND
AS608 V+ → verified supply for the exact module revision
```

Serial rates:

```text
PC ↔ ESP32   : 115200
ESP32 ↔ AS608 : 57600
```

The 57600 rate is configured internally by firmware and should not be entered as the PC COM-port rate.

## 6. Fingerprint scan is not recognized

Try cleaning the sensor, using the enrolled finger consistently, checking that the fingerprint count is non-zero, confirming the device connection, and re-enrolling the template if necessary.

### Confidence interpretation

The firmware emits a match only when hardware confidence is at least 50. The Python processor labels recorded matches using its default configurable threshold of 100:

| Confidence | Status |
| ---: | --- |
| >= 100 | GOOD MATCH |
| 50-99 | WEAK MATCH |

A WEAK MATCH is still recorded by the current processor.

## 7. Repeated scans

DSIS has two duplicate protections: the firmware waits approximately 2 seconds after a scan cycle, while the Python processor suppresses the same fingerprint during the application cooldown, default 10 seconds.

## 8. Enrollment fails

Check that the same finger is used for both captures, the finger is removed between captures, the sensor is powered and stable, and the serial connection remains active.

The local student profile is saved only after the device reports successful fingerprint storage.

## 9. Delete fails

The v3 workflow is device-first: DELETE:<id> is sent to the ESP32, and the local profile is removed only after confirmed device success. A failed hardware deletion leaves the local profile intact.

The maintained firmware calls loadModel() before deleteModel() to reduce false-success behavior for missing templates.

## 10. Wipe problems

**WIPE is destructive. Create a database backup first.**

The v3 workflow expects device WIPE success, linked local student/attendance cleanup, and a fingerprint-count refresh.

If the device reports success but local cleanup fails, DSIS reports that partial state. Do not assume the hardware and database are synchronized until the operation completes.

## 11. Automatic reconnect

Auto-reconnect is enabled by default. Current defaults include up to five reconnect retries and a base delay of two seconds; the serial implementation also caps individual delays.

Check the logs for messages such as Attempting reconnect, Auto-reconnect attempt failed, Auto-reconnect successful, and Auto-reconnect failed after maximum retries.

## 12. Logs and diagnostics

Default log directory: data/logs/

Per-run files use a pattern similar to fingerprint_attendance_YYYYMMDD_HHMMSS.log.

To inspect detected serial ports:

```powershell
python -c "from python.core.device_discovery import list_serial_ports; print(list_serial_ports())"
```

## 13. Software validation

```powershell
node --check python/gui_web/web/app.js
python -m compileall python
python -m pytest -q
```

## 14. Guarded hardware test

```powershell
$env:DSIS_RUN_HARDWARE = "1"
$env:PYTHONPATH = "$PWD\python"
python -m pytest -q tests/physical_esp32_smoke.py
```

Run hardware tests only against an approved test device and test data set. Avoid destructive actions against production fingerprints or student data.

## 15. Common mistakes

- setting the PC COM-port baud to 57600 instead of 115200;
- leaving Arduino Serial Monitor open;
- using a historical standalone firmware sketch with v3;
- assuming COM4 or COM5 is universal;
- assuming WEAK MATCH means the event was rejected;
- wiping the device without a fresh database backup;
- restoring a database without preserving the current database first.

For implementation details, see [v3 System Architecture](../Architecture/v3-system.md) and [v3 Workflows](../UserGuide/v3-workflows.md).

Last reviewed: 2026-09-20.