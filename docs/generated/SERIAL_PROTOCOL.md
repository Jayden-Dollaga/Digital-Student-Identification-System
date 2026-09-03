# Serial Protocol Audit

## Protocol overview

The communication between the desktop app and the ESP32 occurs over a UART serial link.
It supports two overlapping protocol styles:

1. Legacy text protocol (human-readable, older UI compatibility).
2. Structured JSON protocol (newer device discovery and attendance event support).

The Python application handles both styles for backward compatibility.

## Discovery handshake

- Command: `ID?` (sent by Python during automatic or user-triggered serial discovery).
- Expected response: JSON with device metadata.
- Validation checks include:
  - `device` equals `Digital Student Identification System`
  - `protocol` version is present and >= 1

### Metadata fields

- `device`
- `board`
- `firmware`
- `protocol`
- `sensor`
- `serial_number`

The handshake is implemented in `python/core/device_discovery.py` and consumed by `python/core/serial_handler.py`.

## Runtime commands

The host sends uppercase commands terminated with newline, for example:

- `SCAN\n`
- `STOP\n`
- `ENROLL\n`
- `ENROLL:5\n`
- `DELETE:3\n`
- `WIPE\n`
- `LIST\n`

The command wrappers are defined in `python/core/commands.py`, which ensures valid parameter values.

## Scan event flow

### JSON attendance messages

The firmware emits JSON lines during scan mode:

- `{"type":"attendance","event":"match","id":1,"confidence":223}`
- `{"type":"attendance","event":"unknown"}`
- `{"type":"attendance","event":"low_confidence","confidence":42}`

The Python processor uses `parse_json_line()` to parse these lines and `AttendanceProcessor` to decide whether to record an event.

### Legacy text scan inputs

The Python parser accepts these text-based scan results for compatibility with historical firmware:

- `ID:1`
- `CONFIDENCE:223`
- `UNKNOWN`
- `LOW_CONFIDENCE:42`

The maintained all-in-one firmware emits JSON attendance events. `python/core/attendance.py` can parse both styles and applies a cooldown to avoid duplicate logging.

## Connection lifecycle

- The desktop app can connect to a user-selected or auto-detected COM port.
- `SerialHandler.connect()` may perform discovery first, then open the serial port.
- `SerialHandler.read_line()` buffers raw bytes and returns complete lines.
- `SerialHandler.disconnect()` sends a host disconnect status and closes the port.

## Error and ignore behavior

- Lines containing known firmware prompts or help text are ignored by `SerialHandler.should_ignore()`.
- The app logs errors and triggers reconnect logic when serial operations fail.

## Recommendations

- Use JSON messages wherever possible for structured event handling.
- Preserve backward compatibility by continuing to support legacy text output in the firmware and Python parser.
