# DSIS Installation and Daily-Use Guide

This guide covers the maintained DSIS v3 HTML/pywebview application on Windows, including one-time firmware setup and normal daily operation.

## 1. One-time prerequisites

Prepare:

- Windows PC;
- Python installation suitable for the repository requirements;
- Arduino IDE with ESP32 board support;
- ESP32 WROOM-32 development board;
- AS608 fingerprint sensor;
- data-capable USB cable;
- correct USB-to-serial driver for the board.

## 2. Install Python dependencies

From the repository root:

```powershell
python -m pip install -r requirements.txt
```

The repository also provides `install_requirements.bat`, which can create or reuse `.venv`. For an explicit virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

## 3. Install the USB driver

Open **Device Manager → Ports (COM & LPT)** and identify the board's USB bridge.

Common families include CP210x, CH340/CH341, CH9102, and FTDI. Native-USB ESP32 variants can use USB CDC or USB-JTAG and are not the project's verified target.

Python dependencies do not install Windows USB drivers.

## 4. Wire the AS608

| AS608 | ESP32 |
| --- | --- |
| TX | GPIO14 (UART2 RX) |
| RX | GPIO27 (UART2 TX) |
| GND | GND |
| V+ | Verified supply for exact module revision |

PC ↔ ESP32 uses 115200 baud. ESP32 ↔ AS608 uses 57600 baud internally.

Do not assume every AS608 breakout has identical voltage regulation. Verify the module revision before powering it.

See [Wiring](../Hardware/wiring.md) for the detailed pinout and power notes.

## 5. Upload the maintained firmware

Open `firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino` in Arduino IDE.

Select **ESP32 Arduino → ESP32 Dev Module** for the documented WROOM-32 target.

The maintained sketch is the supported firmware path. Historical standalone sketches and `firmware/prebuilt/attendance_v1.0.bin` are not substitutes.

The current sketch advertises firmware 1.0.10 and protocol 1.

## 6. Start DSIS

From the repository root:

```powershell
python run_web_gui.py
```

or:

```text
run_web_gui.bat
```

The v3 application opens a native pywebview window. No browser or local HTTP server is required.

## 7. Complete first-run setup

The wizard proceeds through:

1. password;
2. device;
3. schedule;
4. branding.

The first-run password must be at least 8 characters, must be confirmed, has no built-in default value, and is stored as a salted PBKDF2-HMAC-SHA256 hash using a 16-byte random salt and 310,000 iterations.

Device, schedule, and branding steps persist their completion state in `data/settings.json`.

## 8. Connect the board

1. Close Arduino Serial Monitor and other serial terminals.
2. Connect the ESP32.
3. Click **Connect** in DSIS.
4. Leave auto-detection enabled unless a manual port is necessary.
5. Confirm device metadata and fingerprint count.

A COM port is accepted only after the DSIS identity handshake succeeds.

## 9. Daily workflow

Arduino IDE is not required for normal attendance operation.

```text
Launch DSIS
    ↓
Connect ESP32
    ↓
Verify metadata + fingerprint count
    ↓
Enroll students if needed
    ↓
Start SCAN
    ↓
Fingerprint event
    ↓
Attendance stored in SQLite
    ↓
Review Dashboard / Attendance / Reports
```

Press **STOP** before enrollment, deletion, or wipe operations.

## 10. Roles

| Role | Default permissions |
| --- | --- |
| Administrator | scan, enroll, delete, wipe, export, backup, restore, attendance evaluation, calendar management |
| Teacher | scan, export, backup, attendance evaluation |
| Guest | scan, attendance evaluation |

Authenticated non-guest sessions expire after 600 seconds of inactivity by default.

## 11. Attendance evaluation

The Dashboard supports Day, Monday-Sunday Week, and Calendar Month evaluation.

Evaluation counts distinct attendance dates per student. The observed-day denominator is based on attendance activity in the selected range rather than every empty calendar date.

Category bands:

| Rate | Category |
| ---: | --- |
| 90-100% | Excellent |
| 75-89% | Good |
| 50-74% | Needs attention |
| below 50% | Low attendance |

CSV export of evaluation requires the `export` permission.

## 12. Backups

Manual and automatic database backups are stored under `data/backups/`.

The default automatic backup interval is 25 minutes.

Create a fresh backup before wipe, restore, or database maintenance.

## 13. Logs

Operational logs are written to `data/logs/` when file logging is enabled. Per-run files use a timestamped `fingerprint_attendance_YYYYMMDD_HHMMSS.log` pattern.

## 14. Installation validation

Software:

```powershell
python -m pytest -q
python -m compileall python
node --check python/gui_web/web/app.js
```

Hardware:

- identity handshake;
- fingerprint count;
- scan entry/exit;
- enrollment cancellation;
- successful enrollment with a test finger;
- deletion;
- wipe;
- disconnect/reconnect.

## 15. Common failure points

### COM port unavailable

Check the Windows driver, USB cable, and whether another application owns the port.

### Sensor unavailable

Check GPIO14/GPIO27 wiring, sensor power, and the internal 57600-baud UART configuration.

### Device rejected

Verify that the maintained all-in-one firmware is installed and that `ID?` returns the DSIS identity and supported protocol.

### Unexpected weak attendance result

Review the configurable application `min_confidence`. A WEAK MATCH is still recorded by the current attendance processor.

## Related documentation

- [v3 Workflows](v3-workflows.md)
- [Project Overview](project-overview.md)
- [Hardware Connections](../Hardware/hardware-connections.md)
- [v3 Architecture](../Architecture/v3-system.md)
- [Troubleshooting](../Troubleshooting/README.md)

Last reviewed: 2026-09-20.