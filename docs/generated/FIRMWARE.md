# Firmware Audit

## Main firmware sketch

- `firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino`
  - Primary firmware for the ESP32 attendance controller.
  - Supports enrollment, deletion, wiping, listing, scanning, and host status updates.
  - Uses `Adafruit_Fingerprint` with a hardware serial port on the ESP32.
  - Controls a single onboard LED via PWM with prioritized state transitions.

## Command set

- `ENROLL` or `ENROLL:N` — start enrollment for the next available ID or specified ID.
- `DELETE:N` — delete fingerprint ID `N`.
- `WIPE` — delete all stored fingerprints.
- `LIST` — report stored fingerprint count.
- `SCAN` — enter attendance scan mode.
- `STOP` — stop scan mode and return to command mode.
- `ID?` — handshake command from the Python app to verify the target device.

## Serial output

### Legacy plain-text outputs

- `READY` — board boot completed.
- `ID:N` — fingerprint match found with ID `N`.
- `CONFIDENCE:N` — confidence score after a match.
- `UNKNOWN` — fingerprint not recognized.
- `SCAN_MODE` / `CMD_MODE` — current operating mode.

### JSON outputs

- `{"type":"status","state":"SCAN_MODE"}` — scan mode entered.
- `{"type":"status","state":"CMD_MODE"}` — command mode entered.
- `{"type":"attendance","event":"match","id":N,"confidence":C}` — successful fingerprint match.
- `{"type":"attendance","event":"unknown"}` — unknown fingerprint scan.
- `{"type":"attendance","event":"low_confidence","confidence":C}` — low confidence scan.

## Device metadata handshake

The firmware responds to `ID?` with JSON metadata including:

- `device`: `Fingerprint Attendance`
- `board`: hardware platform identifier
- `firmware`: firmware version
- `protocol`: protocol version number
- `sensor`: sensor model string
- `serial_number`: optional board serial

This handshake is used by `python/core/device_discovery.py` to identify the correct ESP32 among available serial ports.

## Hardware integration

- Uses ESP32 pins `14` (RX from sensor) and `27` (TX to sensor).
- Uses onboard LED pin `2` managed through PWM.
- Supports a sensor cooldown of 2000ms between scans.

## Observations

- Firmware combines multiple phase sketches into one consolidated sketch.
- LED state management is centralized with priority-based temporary and persistent states.
- JSON support is designed for forward compatibility with the Python host.
