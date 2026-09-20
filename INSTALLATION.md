# DSIS Installation Guide

> This guide covers the maintained v3 HTML/pywebview runtime. Qt and CustomTkinter instructions found under archive paths are historical reference only.

This is the repository-level installation guide for the maintained **DSIS v3 HTML/pywebview application**.

For the most detailed operator walkthrough, see [docs/UserGuide/installation-guide.md](docs/UserGuide/installation-guide.md).

## Supported environment

The verified target is:

- Windows
- ESP32 WROOM-32 development board
- Arduino IDE for firmware upload
- AS608 fingerprint sensor
- Python environment using the repository requirements
- USB serial connection from the PC to the ESP32

The current source launcher is:

```powershell
python run_web_gui.py
```

The Windows convenience launcher is:

```text
run_web_gui.bat
```

The former Qt and CustomTkinter applications remain archived and are not the supported v3 launchers.

## 1. Install software

Install Python and then install the repository dependencies:

```powershell
python -m pip install -r requirements.txt
```

The repository also provides `install_requirements.bat`. It can create and reuse a project-local `.venv` and install the requirements there.

For a clean virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

### Dependency roles

| Package | Purpose |
| --- | --- |
| pywebview | Active v3 native desktop window |
| pyserial | PC ↔ ESP32 serial communication |
| openpyxl | Spreadsheet export support used by reporting helpers |
| matplotlib | Report/chart generation |
| Pillow | Image-related helpers and legacy UI support |
| PySide6 | Archived v2 Qt UI/tests |
| CustomTkinter | Archived v1 UI/tests |
| pytest / pytest-forked | Automated testing |
| PyInstaller | Windows packaging |

The legacy UI dependencies are not required for a source-only v3 runtime if you install a reduced environment manually.

## 2. Install the ESP32 USB driver

Windows needs a driver for the board's USB interface. The driver depends on the actual bridge chip, not merely the fact that the board is an ESP32.

Check:

### Device Manager: Ports (COM & LPT)

Common families:

- CP210x
- CH340 / CH341
- CH9102
- FTDI
- Native USB on some ESP32 variants

See [USB Serial Drivers](docs/UserGuide/installation-guide.md#41-usb-to-uart-driver) for vendor references and native-USB notes.

> Installing Python packages does not install Windows USB drivers.

## 3. Wire the AS608

The maintained firmware expects the documented UART arrangement:

| AS608 | ESP32 |
| --- | --- |
| TX | GPIO14 (UART2 RX) |
| RX | GPIO27 (UART2 TX) |
| GND | GND |
| V+ | Power required by the exact sensor module revision |

TX and RX are crossed because the ESP32 receives the sensor's TX and transmits on the sensor's RX.

Do not assume every AS608 breakout uses the same power circuitry. Check the label or documentation for the exact module revision.

See:

- [Hardware connections](docs/Hardware/hardware-connections.md)
- [Wiring guide](docs/Hardware/wiring.md)

## 4. Upload the maintained firmware

Open:

`firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino`

in Arduino IDE.

Use **ESP32 Dev Module** for the documented ESP32 WROOM-32 target.

The maintained firmware currently identifies itself as:

- Device: Digital Student Identification System
- Board: ESP32
- Firmware: 1.0.10
- Sensor: AS608
- Protocol: 1

The host serial connection is **115200 baud**.

The internal ESP32 ↔ AS608 UART is **57600 baud** and is configured by the firmware; the desktop application does not use 57600 for its COM-port connection.

The current firmware supports:

```text
ID?
SCAN
STOP
LIST
ENROLL
ENROLL:<id>
DELETE:<id>
WIPE
STATUS:<state>
```

See [Firmware variants](docs/Hardware/firmware-variants.md) for the supported sketch and historical firmware utilities.

## 5. Launch DSIS

From the repository root:

```powershell
python run_web_gui.py
```

or:

```text
run_web_gui.bat
```

The application creates a native pywebview window and loads the web UI from `python/gui_web/web/`.

No local web server is required.

## 6. Complete first-run setup

The v3 first-run wizard has four logical stages:

1. **Password** — create the initial administrator password.
2. **Device** — connect or intentionally skip device connection for later.
3. **Schedule** — confirm the attendance schedule.
4. **Branding** — configure the school/application name and theme.

There is **no default administrator password**. The password is created during first-run setup and must be at least 8 characters long.

The password is stored as a salted PBKDF2-HMAC-SHA256 hash. The configured implementation uses a 16-byte random salt and 310,000 PBKDF2 iterations.

Steps 2-4 persist their completion state in `data/settings.json`, so an interrupted wizard resumes from the unfinished step.

## 7. Confirm the connection

After the board is connected:

1. Close Arduino Serial Monitor and other serial terminals.
2. Click **Connect** in DSIS.
3. Leave auto-detection enabled unless a manual port is required.
4. Confirm that DSIS receives valid device metadata.
5. Confirm that the fingerprint count is displayed.
6. Start and stop scan mode once before normal use.

A connection is accepted only after the device answers the DSIS identity handshake.

## 8. Daily use

The daily workflow does not require Arduino IDE.

```text
Power / connect ESP32
        ↓
Windows exposes COM port
        ↓
Start run_web_gui.bat
        ↓
DSIS connects to ESP32
        ↓
Enroll students
        ↓
Start SCAN
        ↓
Fingerprint match
        ↓
Attendance stored in SQLite
        ↓
Dashboard / Reports / Evaluation
```

Keep Arduino Serial Monitor closed while DSIS owns the COM port.

## 9. Runtime data

By default, DSIS uses the local `data/` directory for:

- `data/attendance.db` — SQLite database
- `data/settings.json` — saved settings/authentication record
- `data/backups/` — database snapshots
- `data/logs/` — per-run logs when file logging is enabled
- `data/charts/` — generated chart output
- `data/exports/` — exported report files

See [Runtime Data](docs/Development/runtime-data.md) for the data-handling model.

## 10. Validate the installation

Software checks:

```powershell
python -m pytest -q
python -m compileall python
node --check python/gui_web/web/app.js
```

Hardware checks require a real ESP32 and AS608:

- identity handshake
- fingerprint count
- scan mode entry/exit
- enrollment cancellation
- successful enrollment
- deletion
- wipe
- reconnect behavior

Do not use historical sketches or the `BIN_PLACEHOLDER` file as substitutes for the maintained all-in-one firmware.

## Troubleshooting

Start with [docs/Troubleshooting/README.md](docs/Troubleshooting/README.md).

The most common causes of connection failure are:

- wrong or stale COM port
- missing USB driver
- serial monitor holding the port open
- incorrect firmware
- incorrect AS608 wiring
- unstable USB/power connection

Last reviewed: 2026-09-20.
