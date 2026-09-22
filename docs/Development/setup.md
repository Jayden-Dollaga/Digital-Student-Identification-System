# Development Setup

## Active source tree

The maintained application is launched with `run_web_gui.py` or `run_web_gui.bat`.

    python/
    ├── gui_web/
    │   ├── main_web.py
    │   ├── api.py
    │   └── web/
    │       ├── index.html
    │       ├── app.js
    │       └── styles.css
    ├── core/
    ├── services/
    ├── config.py
    └── settings_store.py

The maintained firmware is:

    firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino

## Install and run

    python -m pip install -r requirements.txt
    python run_web_gui.py

## Runtime assumptions

- Windows is the supported desktop environment.
- pywebview hosts the frontend.
- pyserial provides COM communication.
- SQLite stores local application data.
- Firmware is flashed separately.
- PC ↔ ESP32 is 115200 baud.
- ESP32 ↔ AS608 is 57600 baud.

## Source boundaries

UI code should use `gui_web.api.Api` rather than accessing the database, serial object, or filesystem directly.

Hardware protocol behavior belongs to the firmware plus `core.serial_handler`, `core.device_discovery`, and `core.commands`.

Authorization belongs to `core.permissions` and privileged call sites, not only frontend button visibility.

## Archived code

v1 CustomTkinter and v2 Qt source are preserved under `archive/legacy-ui/`. Do not copy those trees into the active source tree when developing v3.
