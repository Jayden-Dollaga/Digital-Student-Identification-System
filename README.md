# Digital Student Identification System

DSIS is a Windows desktop attendance system for schools and training centers. An ESP32 and AS608 fingerprint sensor handle enrollment and identification; the Python application manages student records, attendance history, reports, backups, and serial communication.

## Features

- Fingerprint enrollment, matching, deletion, and device wipe
- SQLite student and attendance records
- HTML/pywebview dashboard, attendance, students, reports, logs, and settings interface
- Attendance cooldown handling and confidence-aware scan processing
- Day, week, and month attendance evaluation with category bands and CSV export
- CSV/report exports and database backups with role-based UI permissions
- ESP32 device discovery, connection status, firmware assistance, and serial diagnostics

## Screenshots

![DSIS Main](docs/UserGuide/images/Screenshot_2026-08-28_014145.png)

![Fingerprint Report Page](docs/UserGuide/images/Screenshot_2026-08-28_014206.png)

## Quick Start

1. Install Python and project dependencies:

   ```text
   python -m pip install -r requirements.txt
   ```

2. Install the USB serial driver that matches the bridge chip on your ESP32 board. CP210x is correct for Silicon Labs boards; CH340/CH341, CH9102, FTDI, and native-USB boards need their corresponding driver or Windows support. See [Installation](INSTALLATION.md).

3. Upload the all-in-one firmware once using Arduino IDE. See [Installation](INSTALLATION.md) for wiring, board, and firmware details.

4. Connect the ESP32 with a data-capable USB cable, close other serial monitors, and launch the active v3 webview application:

   ```text
   run_web_gui.bat
   ```

For packaged Windows deployment, see [Portable Build](PORTABLE_BUILD.md). For daily workflows, see the [v3 workflow guide](docs/UserGuide/v3-workflows.md). For connection problems, see [Current Troubleshooting](docs/Troubleshooting/README.md). Contributors should start with [Contributing](CONTRIBUTING.md) and [Release Guide](RELEASE.md).

The PC-to-ESP32 USB serial connection uses **115200 baud**. The separate ESP32-to-AS608 sensor UART uses **57600 baud** internally; do not select 57600 in the desktop app.

The Dashboard includes Attendance Evaluation for day, week, or month windows. It counts distinct attendance dates per student against observed school days, groups rates as Excellent, Good, Needs attention, or Low attendance, and can export the current evaluation as a CSV file. Evaluation and export require the role's `export` or `backup` permission.

## USB Serial Drivers

Windows needs a driver for the USB interface chip on the board, not for the ESP32 brand itself. Check **Device Manager > Ports (COM & LPT)** and install the matching vendor driver if the board does not appear as a COM port:

- [Silicon Labs CP210x VCP drivers](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers) for CP210x boards, including the CP210x Universal Windows Driver.
- [WCH CH34x drivers](https://www.wch-ic.com/downloads/CH343SER_ZIP.html) for CH340/CH341 boards.
- WCH CH9102 driver for boards identified as CH9102; use the driver supplied by the board manufacturer or WCH.
- [FTDI VCP drivers](https://ftdichip.com/drivers/vcp-drivers/) for FT232-family boards.
- Native-USB ESP32-S2/S3/C3 boards may use USB CDC or USB-JTAG instead of a USB-UART bridge. Their support depends on the board and firmware configuration and is not verified by this project.

Installing Python packages does not install Windows USB drivers. The application can use an unfamiliar adapter when Windows exposes it as a COM port and the device answers the DSIS handshake.

## Active Interfaces

The maintained desktop interface is the HTML/pywebview v3 application launched by [run_web_gui.py](run_web_gui.py) or [run_web_gui.bat](run_web_gui.bat). The former Qt and CustomTkinter interfaces are archived under [archive/legacy-ui/](archive/legacy-ui/) and are not current launchers.

### UI Prototypes

The UI concepts in [`tests/Prototype/`](tests/Prototype/) are isolated previews. They do not start the live serial or database workflow and do not replace the maintained v3 webview application. See the [UI prototype guide](docs/Development/ui-prototypes.md) for the full comparison and testing notes.

```text
python tests/Prototype/run_qt_prototype.py
```

It includes mock identification data, navigation, device status, scan controls, result details, and a compact density switch for evaluating the layout before integration.

An alternate hybrid concept combines that identification workspace with the production app's Dashboard, Attendance, Students, Reports, and Logs structure:

```text
python tests/Prototype/run_hybrid_prototype.py
```

The Windows 11 Task Manager-inspired comparison variant adds icon navigation, a lighter utility palette, and an icon-only compact rail:

```text
python tests/Prototype/run_task_manager_variant.py
```

The original-style reconstruction is available separately for direct comparison with the current application's six-page dark shell:

```text
python tests/Prototype/original_ui.py
```

For a display-only preview composed from the actual Qt pages in `python/gui_qt` (without starting serial workers), run:

```text
python tests/Prototype/run_original_ui_display.py
```

To view the actual Qt pages with the Task Manager-inspired shell and navigation icons combined:

```text
python tests/Prototype/run_combined_ui.py
```

## Project Structure

| Path | Purpose |
| --- | --- |
| `python/` | Python application, services, serial handling, database, and UI code |
| `firmware/` | ESP32 and AS608 Arduino sketches |
| `data/` | Runtime settings, database, backups, logs, and charts |
| `tests/` | Automated regression and integration tests |
| `tools/` | Diagnostics, packaging helpers, and maintenance scripts |
| `docs/` | User, architecture, hardware, development, security, and generated documentation |
| `archive/` | Historical and experimental material retained for reference |

See the [documentation index](docs/INDEX.md) and [documentation map](docs/Development/documentation-map.md) for the full map.

## License

See [LICENSE](LICENSE).

Last reviewed: 2026-09-11, against commit `aa457e0`
