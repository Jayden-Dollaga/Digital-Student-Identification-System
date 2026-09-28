# Installation Guide

This is the installation guide for the maintained DSIS v3 HTML/pywebview desktop application.

> Historical CustomTkinter and Qt instructions are archive-only. They are not the supported product path for the current build.

## Supported environment

- Windows 10 or Windows 11
- Python 3.10+ (use the repo virtual environment if available)
- ESP32 development board
- AS608 fingerprint sensor
- RC522 RFID reader (optional hardware on the same maintained firmware)
- USB-to-serial driver for the ESP32 board
- Arduino IDE for firmware upload

## 1. Install the Python environment

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If you are using the repository-provided helper:

```powershell
install_requirements.bat
```

## 2. Install the correct USB driver

The board's USB bridge chip determines the required driver. Common families include CP210x, CH340/CH341, CH9102, FTDI, and native USB variants.

If Windows does not expose a COM port, open Device Manager and confirm the board is visible under Ports (COM & LPT) or USB Serial Device.

See [docs/Hardware/drivers-and-ports.md](docs/Hardware/drivers-and-ports.md) for the OS-specific guidance.

## 3. Wire the hardware

The active sketch expects the AS608 UART on GPIO14 and GPIO27, and the RC522 SPI pins as defined in the firmware.

The host serial link to the application is 115200 baud. The internal ESP32-to-AS608 UART is 57600 baud.

See [docs/Hardware/wiring.md](docs/Hardware/wiring.md) and [docs/Hardware/firmware.md](docs/Hardware/firmware.md).

## 4. Upload the maintained firmware

Open the sketch at:

`firmware/ESP32_DSIS_AllInOne/ESP32_DSIS_AllInOne.ino`

in Arduino IDE. Select the ESP32 board package matching the target board and flash it with the same settings used by the project:

- board: ESP32 Dev Module or equivalent WROOM board
- firmware ID: 1.6.2
- protocol: 1
- host serial: 115200
- sensor UART: 57600

After upload, keep Arduino Serial Monitor closed while DSIS is running, because the app owns the serial connection.

## 5. Launch the app

From the repo root:

```powershell
python run_web_gui.py
```

Or use the Windows launcher:

```powershell
run_web_gui.bat
```

The app opens the v3 pywebview window and loads the HTML/JS/CSS from `python/gui_web/web/`.

## 6. Complete first-run setup

On first launch, DSIS requires a full password/setup flow. The steps are:

1. Password
2. Device
3. Schedule
4. Branding

There is no built-in default administrator password. The password must be at least 8 characters and is stored with a salted PBKDF2-HMAC-SHA256 hash.

The session is guest-by-default until an admin password is set and verified. The setup flags are persisted in `data/settings.json` so the wizard resumes correctly after interruption.

See [docs/UserGuide/first-run-wizard.md](docs/UserGuide/first-run-wizard.md).

## 7. Confirm connection and scan behavior

1. Connect the ESP32 to the PC.
2. Open the app.
3. Select or allow auto-detect for the COM port.
4. Click Connect.
5. Confirm that DSIS reports the board metadata and a valid fingerprint count.
6. Start scan mode and stop it once to confirm the command path is working.

## 8. Runtime data locations

The app writes to the local `data/` directory:

- `data/attendance.db` — SQLite database
- `data/settings.json` — UI settings and auth metadata
- `data/backups/` — timestamped database snapshots
- `data/logs/` — rotating runtime logs
- `data/exports/` — CSV/report exports

Protect this directory with normal Windows access control because it contains student attendance data and administrative auth state.

## 9. Validate the installation

Recommended checks:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest -q
python -m compileall python
node --check python/gui_web/web/app.js
```

See [docs/Development/testing.md](docs/Development/testing.md) and [PORTABLE_BUILD.md](PORTABLE_BUILD.md) for more validation guidance.

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

## Documentation coverage

For the source-backed details behind this installation procedure, see [the whole-app inventory](docs/generated/APP_INVENTORY.md), [first-run wizard](docs/UserGuide/first-run-wizard.md), [drivers and ports](docs/Hardware/drivers-and-ports.md), and [firmware](docs/Hardware/firmware.md).

The current v3 host/device split is **115200 baud PC ↔ ESP32** and **57600 baud ESP32 ↔ AS608**. The desktop application does not connect directly to the AS608.

Runtime data under `data/` is local and sensitive: protect `settings.json`, `attendance.db`, backups, logs, exports, and charts.
