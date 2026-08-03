# Installation guide

## Standard setup

1. Install Python 3.10 or newer.
2. Open a command prompt in the repository root.
3. Run the bootstrap script:
   - `tools\portable_bootstrap.bat`
4. Launch the legacy desktop GUI with:
   - `python python/gui/app.py`
5. Launch the newer Qt interface from the repository root with:
   - `python run_qt_gui.py`

If `python` is not on PATH, use the Windows launcher:

- `py -3 python/gui/app.py`
- `py -3 run_qt_gui.py`

## ESP32 detection without Arduino IDE

If the app cannot see your ESP32, you usually need the USB-to-serial driver for the board and a working COM port.

- USB-to-serial driver for the ESP32 board (often CP210x or CH340 depending on the board)
- Python dependencies from the bootstrap script

### What to check

1. Plug the ESP32 into the PC with a good USB cable.
2. Open Device Manager and look for a COM port under Ports (COM & LPT) or USB Serial Device.
3. If a driver is missing, install the board's USB driver from the board manufacturer or Espressif support pages.
4. Try another USB cable or port if the board still does not appear.
5. Press the EN/RST button once after plugging it in.

If you plan to upload firmware, these board URLs are commonly used in the Arduino IDE:

- <https://dl.espressif.com/dl/package_esp32_index.json>
- <https://github.com/espressif/arduino-esp32>

And the fingerprint library:

## Portable deployment

For field testing on another machine, package the application with PyInstaller and copy the output folder to a USB drive.
