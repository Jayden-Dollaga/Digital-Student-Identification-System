# Active Firmware

The maintained embedded program is:

    firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino

## Current firmware identity

| Field | Value |
| --- | --- |
| Device identifier | Digital Student Identification System |
| Board | ESP32 |
| Firmware | 1.0.10 |
| Sensor | AS608 |
| Protocol | 1 |
| Host serial | 115200 baud |
| Sensor UART | 57600 baud |
| AS608 RX/TX | GPIO 14 / GPIO 27 |
| Fingerprint ID range | 1–127 |

## Boot

The firmware starts host serial at 115200, prints device identity JSON, starts the AS608 UART at 57600, verifies the sensor, reports the stored fingerprint count, prints command help, and emits READY/status output.

The boot identity JSON contains the device identifier, board, firmware version, sensor, protocol, and ESP32 eFuse-derived serial number.

If AS608 initialization fails, the firmware enters its sensor-error path and does not continue normal command processing.

## Commands

| Command | Behavior |
| --- | --- |
| `ID?` | Return device identity JSON |
| `SCAN` | Enter fingerprint scan mode |
| `STOP` | Return to command mode / cancel active operation |
| `LIST` | Report stored fingerprint count |
| `ENROLL` | Use the next free fingerprint ID |
| `ENROLL:id` | Enroll explicit ID 1–127 |
| `DELETE:id` | Delete one fingerprint ID |
| `WIPE` | Delete all fingerprint templates |
| `STATUS:state` | Update host/status LED state |

The firmware also accepts the JSON status form:

    {"type":"status","state":"HOST_CONNECTED"}

and the equivalent HOST_DISCONNECTED state.

## Enrollment

Automatic enrollment searches IDs 1 through 127 and uses the first free slot. Explicit enrollment accepts only IDs 1 through 127.

The user must place the same finger for the two capture stages. The firmware creates the fingerprint model and stores it in the selected AS608 slot.

## Attendance events

Match:

    {"type":"attendance","event":"match","id":1,"confidence":223}

Unknown:

    {"type":"attendance","event":"unknown"}

Low confidence:

    {"type":"attendance","event":"low_confidence","confidence":42}

The firmware emits a match when confidence is at least 50. Values below that floor generate the low-confidence event.

## Cooldown

The device waits 2 seconds after a matched or low-confidence scan and 1 second after an unknown scan before processing another scan.

The Python desktop processor has a separate configurable cooldown, default 10 seconds.

## LED/status states

The LED manager contains states for boot, ready, scan, success, enrollment, firmware, error, database error, communication error, host connected, host disconnected, and sleep.

HOST_CONNECTED and HOST_DISCONNECTED are status indicators only. They are not an authorization gate.

## Compatibility note

The Python parser accepts both these structured JSON events and legacy human-readable serial lines. Older firmware sketches are preserved elsewhere in the repository and are historical, not automatically interchangeable with this maintained protocol.
