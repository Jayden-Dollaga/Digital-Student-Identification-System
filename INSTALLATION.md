# Installation

The maintained installation and daily-use instructions are in the
[DSIS User Guide](docs/UserGuide/installation-guide.md).

For a quick Windows launch from the repository root:

```text
run_qt_gui.bat
```

Install dependencies first with:

```text
python -m pip install -r requirements.txt
```

Before connecting the board, install the Windows driver matching its USB interface chip. CP210x is only for Silicon Labs CP210x boards; other common families are CH340/CH341, CH9102, and FTDI. Identify the chip in **Device Manager > Ports (COM & LPT)**. See the [driver section in the User Guide](docs/UserGuide/installation-guide.md#41-usb-serial-driver) for vendor links and native-USB notes.

The verified target is an ESP32 WROOM-32 selected as **ESP32 Dev Module** in Arduino IDE. Native-USB ESP32 variants are not verified by this project.

See [Troubleshooting](docs/TROUBLESHOOTING.md) for COM-port and firmware checks.

Last verified: 2026-09-03, against the current `main` branch
