# PROJECT FORENSIC AUDIT

This report is an analysis-only forensic audit of the repository as it exists today. No source files were modified, deleted, or “fixed.” The repository itself is treated as the primary source of truth.

---

## 1. Executive Summary

This project is a fingerprint-based attendance system built around an ESP32 + AS608 sensor, a Python host application, and a SQLite database. The intended flow is:

- the ESP32 reads fingerprints and emits scan or enrollment results over serial,
- the Python layer parses those outputs, logs attendance, and updates the GUI,
- the GUI lets users connect to the device, enroll students, wipe fingerprints, and review attendance records.

What the repository currently shows is a system that is only partially coherent:

- the firmware is a single large sketch with a stateful command parser, LED manager, and fingerprint workflow,
- the Python host contains a newer Qt GUI path and an older CustomTkinter path that coexist,
- the serial protocol supports both legacy text outputs and newer JSON messages,
- the codebase has been refactored repeatedly and now contains competing implementations, duplicated logic, and multiple compatibility layers.

The project is not “dead,” but it is in a fragile state. It can appear to work for simple connection and basic scan scenarios, yet fail in edge cases involving reconnects, enrollment, wipe flows, scan mode transitions, and hardware timing. The main issue is not a single obvious bug; it is architectural drift: firmware, Python, GUI, and documentation have evolved separately and are only partially aligned.

---

## 2. Architecture

### Intended architecture

The architecture implied by the project documentation and core modules is:

```text
ESP32
↓
AS608 sensor
↓
Serial / USB
↓
Python serial layer
↓
Device discovery
↓
Serial worker / thread
↓
GUI
↓
Attendance processor
↓
SQLite database
```

### Actual architecture in the repository

The repository does not follow a single clean path. Instead, it contains three overlapping layers:

1. Firmware layer
   - Main sketch: [firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino](../firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino)
   - Smaller sketches for attendance, enroll, delete, and testing under [firmware](../firmware)

2. Python host layer
   - Core serial handling: [python/core/serial_handler.py](../python/core/serial_handler.py)
   - Device discovery and handshake: [python/core/device_discovery.py](../python/core/device_discovery.py)
   - Attendance parsing and logging: [python/core/attendance.py](../python/core/attendance.py)
   - Database: [python/core/database.py](../python/core/database.py)
   - Command wrappers: [python/core/commands.py](../python/core/commands.py)

3. UI layer
   - Legacy CustomTkinter GUI: [python/gui](../python/gui)
   - Modern Qt GUI: [python/gui_qt](../python/gui_qt)
   - Duplicated redesign scaffolds under [tests/gui_qt_redesign](../tests/gui_qt_redesign) and [tests/gui_qt_redesign (2)](../tests/gui_qt_redesign%20(2))

### Communication paths

- The ESP32 firmware speaks to the AS608 sensor over HardwareSerial and to the host over USB serial.
- The host uses Python serial libraries to open a COM port, send commands, and read text or JSON lines.
- The serial worker in [python/gui_qt/workers/serial_worker.py](../python/gui_qt/workers/serial_worker.py) reads lines in a background thread and emits Qt signals to the UI.
- The attendance processor in [python/core/attendance.py](../python/core/attendance.py) turns raw sensor messages into attendance records.
- The database layer in [python/core/database.py](../python/core/database.py) persists student and attendance rows to SQLite.

### Important architectural divergence

The codebase contains both a legacy and a modern GUI stack, and the firmware supports both text and JSON outputs. That means the system is built as a compatibility layer rather than as a single cohesive design.

---

## 3. Firmware Analysis

### 3.1 Startup sequence

The main firmware sketch in [firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino](../firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino) begins with:

- LED setup and PWM initialization,
- serial baud setup at 115200,
- a one-second boot animation loop using `delay(10)` in `setup()`,
- device identification output,
- sensor initialization over HardwareSerial,
- fingerprint sensor verification,
- template count readout,
- help text,
- `READY` plus JSON status output.

The startup sequence is visible in the code path:

- `setup()`
- `beginLedManager()`
- `mySerial.begin(57600, ...)`
- `finger.begin(57600)`
- `finger.verifyPassword()`
- `finger.getTemplateCount()`
- `printHelp()`
- `Serial.println("READY")`
- `emitJsonStatus("READY")`

### 3.2 Initialization

The firmware initializes:

- the onboard LED as a PWM-controlled output,
- the UART used for the AS608 sensor,
- the fingerprint library object,
- the LED manager state machine,
- the scan mode flag `scanMode` and pending command buffer.

### 3.3 AS608 communication

The firmware uses the Adafruit fingerprint library through `Adafruit_Fingerprint finger = Adafruit_Fingerprint(&mySerial);`.

The core operations are:

- `finger.getImage()`
- `finger.image2Tz()`
- `finger.fingerSearch()`
- `finger.createModel()`
- `finger.storeModel()`
- `finger.deleteModel()`
- `finger.emptyDatabase()`
- `finger.getTemplateCount()`
- `finger.loadModel()`

### 3.4 Command handling

The firmware’s `handleCommand()` accepts:

- `ID?` for device discovery handshake,
- `SCAN`, `STOP`, `LIST`, `WIPE`,
- `ENROLL` and `ENROLL:ID`,
- `DELETE:ID`,
- `STATUS:...` and JSON-formatted status messages.

The command logic changes the mode flags and the LED state but does not implement a fully separate state machine beyond `scanMode` plus the LED manager.

### 3.5 SCAN mode

When `SCAN` is received, the firmware:

- sets `scanMode = true`,
- requests the LED scan state,
- prints a human-readable banner,
- emits `SCAN_MODE` and `{"type":"status","state":"SCAN_MODE"}`.

While in scan mode, `loop()` calls `scanFinger()` repeatedly.

### 3.6 Command mode

When `STOP` is received, the firmware:

- sets `scanMode = false`,
- reverts to the ready LED state,
- prints help text,
- emits `CMD_MODE` and JSON status.

### 3.7 Enrollment

Enrollment is handled in `enrollFinger(int id)` and uses a multi-step procedure:

- prompt for first scan,
- convert image to template slot 1,
- wait for finger removal,
- prompt for second scan,
- convert to template slot 2,
- create model,
- store model,
- report success or failure.

The firmware also has logic to cancel enrollment if it sees new serial input (`checkEnrollmentCancel()`), but that logic is tied to the serial buffer and the loop timing.

### 3.8 Deletion and wipe

- `DELETE:ID` calls `finger.deleteModel(id)`.
- `WIPE` calls `finger.emptyDatabase()`.

Both are relatively simple but lack a robust confirmation/protocol handshake with the host beyond the printed text output.

### 3.9 Fingerprint matching

The matching logic in `scanFinger()` uses:

- `finger.getImage()`
- `finger.image2Tz()`
- `finger.fingerSearch()`

If a match is found and confidence is above the threshold, the firmware emits JSON attendance match. If the confidence is lower, it emits JSON low-confidence. If no match is found, it emits an unknown event.

### 3.10 Attendance events and JSON output

The firmware emits:

- `{"type":"attendance","event":"match","id":x,"confidence":y}`
- `{"type":"attendance","event":"unknown"}`
- `{"type":"attendance","event":"low_confidence","confidence":y}`
- `{"type":"status","state":"SCAN_MODE"}`
- `{"type":"status","state":"CMD_MODE"}`
- `{"type":"status","state":"READY"}`

The code also emits legacy text lines such as `ID:1`, `CONFIDENCE:223`, `UNKNOWN`, and `LOW_CONFIDENCE:42`.

### 3.11 LED state manager

The firmware contains an explicit LED state manager with states such as:

- `LED_BOOTING`
- `LED_READY`
- `LED_SCAN`
- `LED_SUCCESS`
- `LED_ENROLL`
- `LED_FIRMWARE`
- `LED_ERROR`
- `LED_DB_ERROR`
- `LED_COMMUNICATION_ERROR`
- `LED_HOST_CONNECTED`
- `LED_HOST_DISCONNECTED`
- `LED_SLEEP`

The state manager uses a priority table. This is more sophisticated than the rest of the firmware, but the interactions between LED state requests and scan/enroll/host connection events are not fully synchronized with the command state machine.

### 3.12 Host connection status

The firmware understands host status messages via `STATUS:HOST_CONNECTED`, `STATUS:HOST_DISCONNECTED`, and JSON status messages. These are mapped to the LED manager through `handleHostStatus()`.

### 3.13 Firmware update behavior

The repository includes firmware helper logic in [python/core/firmware_helper.py](../python/core/firmware_helper.py) for discovering firmware binaries and uploading them with `esptool`. The firmware itself contains no embedded update mechanism; updates are external to the sketch and handled from Python.

### 3.14 Reset and reboot behavior

The firmware does not contain a deliberate watchdog reset handler or reboot loop logic in the main sketch. The observed repeated startup output would therefore point to an external reset, a hardware issue, or a crash path rather than a normal internal state transition. The repository does not contain evidence of a deliberate “power on reset on scan failure” path.

### 3.15 Serial buffering and timing

The firmware uses `Serial.available()` and `Serial.readStringUntil('\n')` in the loop. It also uses `delay()` and `millis()` in the enrollment and scan paths. The code is not written as an event-driven architecture; it relies on blocking loops for enrollment and short delays for scan cooldowns.

### 3.16 Blocking operations

The firmware blocks in several places:

- boot animation loop,
- enrollment loops waiting for finger capture,
- `delay(SCAN_COOLDOWN)` after a scan,
- repeated polling loops with `delay(50)`.

These blocks are not catastrophic on their own, but they can interact badly with serial input and with host-side reconnect logic.

### 3.17 State machine risk

The firmware has at least three overlapping state concepts:

- command mode vs. scan mode,
- LED state vs. restore state,
- host connection status state.

These concepts are not always mutually exclusive. That makes the firmware vulnerable to state conflicts, especially if scan mode and enrollment mode overlap or if the host sends a status message while the firmware is mid-enrollment.

### 3.18 Error handling

Error handling exists, but it is uneven:

- sensor not found causes an infinite loop with `while (1)` and `updateLed()`,
- enrollment mismatches and failed storage are reported but do not always reset mode cleanly,
- unknown commands are logged but do not force a consistent state reset,
- serial input during enrollment is treated as a cancellation request but can also be queued as a pending command.

### 3.19 Firmware risks that are supported by the code

The code supports the following risk categories:

- reboot loops: possible but not confirmed by code alone; repeated startup output implies a board restart or re-entry into `setup()`
- watchdog resets: not directly implemented in the sketch, but a hardware-side reset remains plausible
- serial corruption: possible because the firmware mixes text and JSON, and the Python parser has to tolerate both
- scan failures: likely due to timing and sensor state interaction, especially during transitions from scan mode to enroll mode
- sensor failures: supported by the explicit sensor-not-found branch and the blocking capture loops
- state-machine conflicts: confirmed by the overlapping command, LED, and host-status states
- LED conflicts: confirmed by the priority-based LED state manager and multiple callers
- command conflicts: confirmed by pending command handling during enrollment
- memory problems: not directly evidenced in the code, but the firmware is simple enough that memory exhaustion is unlikely compared to state and timing problems

---

## 4. Serial Protocol Audit

The repository supports two overlapping protocols: legacy human-readable text and structured JSON. This is a design smell because the same logical operation can be represented in more than one format.

### 4.1 Protocol command/message inventory

| Command / Message | Sender | Receiver | Format | Expected response | State transition | Parser responsible | Error behavior | Style |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ID?` | Python discovery layer | ESP32 | Text command | JSON metadata block | No mode change | [python/core/device_discovery.py](../python/core/device_discovery.py) | Handshake rejected if metadata invalid | Text command + JSON response |
| `SCAN` | Python host or GUI | ESP32 | Text command | Banner text + `SCAN_MODE` + JSON status | Enter scan mode | [python/core/commands.py](../python/core/commands.py) and firmware sketch | No explicit failure path; sets scan mode regardless of hardware readiness | Legacy text + JSON |
| `STOP` | Python host or GUI | ESP32 | Text command | Banner text + `CMD_MODE` + JSON status | Leave scan mode | Same as above | No explicit failure path | Legacy text + JSON |
| `ENROLL` | Python host or GUI | ESP32 | Text command | Enrollment prompts and success/failure messages | Exit scan mode, enter enrollment flow | Firmware sketch | Enrollment can be cancelled or interrupted by new serial input | Legacy text |
| `ENROLL:ID` | Python host or GUI | ESP32 | Text command | Same as above but targeted ID | Same as above | Firmware sketch | ID validated range 1–127 | Legacy text |
| `DELETE:ID` | Python host or GUI | ESP32 | Text command | Success/failure messages | No mode change | Firmware sketch | ID validated range 1–127 | Legacy text |
| `WIPE` | Python host or GUI | ESP32 | Text command | Success/failure message + command mode banner | Leaves scan mode | Firmware sketch | Failure reported as text | Legacy text |
| `LIST` | Python host or GUI | ESP32 | Text command | Stored fingerprint count | Leaves scan mode | Firmware sketch | No explicit failure path | Legacy text |
| `STATUS:HOST_CONNECTED` | Python host | ESP32 | Text command | LED state update | Host connected | Firmware sketch | Unknown values ignored | Legacy text |
| `STATUS:HOST_DISCONNECTED` | Python host | ESP32 | Text command | LED state update | Host disconnected | Firmware sketch | Unknown values ignored | Legacy text |
| `STATUS:DB_ERROR` | Python host | ESP32 | Text command | Temporary LED state update | Not a core runtime state | Firmware sketch | No full protocol semantics beyond LED | Legacy text |
| `STATUS:FIRMWARE` | Python host | ESP32 | Text command | LED state update | Firmware activity | Firmware sketch | No full protocol semantics beyond LED | Legacy text |
| `STATUS:READY` | Python host | ESP32 | Text command | LED state update | Ready state | Firmware sketch | Unknown values ignored | Legacy text |
| `{"type":"status","state":"..."}` | Python host or firmware | Both directions | JSON | Firmware responds by updating LED state; Python parses the state | Mode/status change | [python/core/utils.py](../python/core/utils.py) and [python/gui_qt/workers/serial_worker.py](../python/gui_qt/workers/serial_worker.py) | Invalid JSON is ignored by parser | JSON |
| `{"type":"attendance","event":"match","id":x,"confidence":y}` | ESP32 | Python host | JSON | Attendance processor logs and emits scan event | Attendance recorded | [python/core/attendance.py](../python/core/attendance.py) | Missing fields are ignored | JSON |
| `{"type":"attendance","event":"unknown"}` | ESP32 | Python host | JSON | Unknown scan recorded | Attendance recorded as unknown | [python/core/attendance.py](../python/core/attendance.py) | No extra fields required | JSON |
| `{"type":"attendance","event":"low_confidence","confidence":y}` | ESP32 | Python host | JSON | Low-confidence event ignored or downgraded | No attendance record by default | [python/core/attendance.py](../python/core/attendance.py) | No explicit error path | JSON |
| `Sensor found!` | ESP32 | Host | Text | No state change; printed boot message | Startup / initialization | Serial layer ignores known boot noise | Not treated as a protocol error | Legacy text |
| `Stored fingerprints: N` | ESP32 | Host | Text | Count display | Initialization | Serial layer ignores/prints | No action beyond display | Legacy text |
| `READY` | ESP32 | Host | Text | Host marks device ready | Ready state | [python/main.py](../python/main.py) and worker parser | No special handling beyond state update | Legacy text |
| `SCAN_MODE` | ESP32 | Host | Text | Host enters scan state | Scan mode | [python/gui_qt/workers/serial_worker.py](../python/gui_qt/workers/serial_worker.py) | If line is missed, the UI may remain out of sync | Legacy text |
| `CMD_MODE` | ESP32 | Host | Text | Host leaves scan mode | Command mode | Same as above | Same as above | Legacy text |
| `ID:1`, `CONFIDENCE:223`, `UNKNOWN`, `LOW_CONFIDENCE:42` | ESP32 | Host | Text | Attendance processor updates state | Scan result | [python/core/attendance.py](../python/core/attendance.py) | Missing or out-of-order parts can lead to misattribution | Legacy text |

### 4.2 Protocol inconsistencies

The repository contains multiple protocol inconsistencies:

- The firmware emits both text and JSON for the same logical events.
- The Python parser accepts both forms, but the firmware and host code are not fully synchronized on semantics.
- The host uses a JSON handshake during discovery, while the rest of the runtime is still effectively text-driven.
- The Qt worker handles JSON status lines and legacy `SCAN_MODE` / `CMD_MODE` lines, but the legacy CustomTkinter GUI uses a separate parser and code path.
- The firmware’s `LIST` command prints `CMD_MODE` but does not emit JSON status, while other commands do.

These inconsistencies are a major source of fragility because the same state change can be represented differently depending on which code path runs.

---

## 5. Python Serial Layer

### 5.1 SerialHandler responsibilities

The core serial boundary is implemented in [python/core/serial_handler.py](../python/core/serial_handler.py). It is responsible for:

- port enumeration,
- device discovery and handshake,
- serial connection setup,
- disconnecting cleanly,
- sending commands,
- reading lines from the device,
- background reconnect management.

### 5.2 Reconnect logic

The serial handler has a background reconnect worker and a reconnect counter. It is designed to recover from temporary connection loss. That is a good architecture, but three issues follow from the implementation:

- reconnect state is shared across the connection lifecycle and can be re-entered repeatedly,
- the reconnect worker can run while the user is explicitly trying to connect or disconnect,
- the reconnect loop is triggered from multiple points: connect failures, read errors, send failures, and disconnect cleanup.

### 5.3 Port probing and discovery

The discovery logic in [python/core/device_discovery.py](../python/core/device_discovery.py) is fairly sophisticated:

- it enumerates serial ports,
- scores candidates based on hardware keywords and VID/PID,
- sends an `ID?` handshake,
- validates the returned JSON handshake.

That is good, but it also means the system depends heavily on the device answering a handshake promptly and consistently. If the firmware resets or stalls, discovery can fail and cause the host to repeatedly re-probe ports.

### 5.4 Buffering and reads

The serial handler buffers partial lines and returns complete lines. This is necessary because serial reads can break lines arbitrarily. However, the code uses a small internal buffer and a lock around reads. That should be reliable in regular operation, but it becomes fragile when the device emits a burst of startup text, boot noise, and handshake data.

### 5.5 Threading and locks

The serial handler uses `threading.RLock()` and a background reconnect thread. That is a reasonable design for a background serial service. However, the code mixes connection state, reconnect state, and I/O operations in one object. The result is a large and stateful component with many entry points.

### 5.6 Disconnect behavior

The disconnect path sends `HOST_DISCONNECTED` and `STOP` to the device before closing the port. This is sensible in theory, but it means disconnect can itself trigger more serial output or fail if the device is already unstable.

### 5.7 Likely problems in the serial layer

The code strongly suggests the following issues:

- reconnect loops can be triggered repeatedly when the device is unstable,
- stale COM ports can persist in settings and cause repeated failures,
- the code assumes the device will respond to a handshake and then remain stable,
- the host lacks a fully deterministic notion of “device boot completed” vs. “device still initializing,”
- if the firmware restarts mid-stream, the Python layer may interpret the new boot sequence as a fresh serial session rather than a device reset.

---

## 6. Qt GUI / Threading

### 6.1 Qt architecture

The modern GUI path is implemented under [python/gui_qt](../python/gui_qt). The main window is [python/gui_qt/main_window.py](../python/gui_qt/main_window.py), and the worker is [python/gui_qt/workers/serial_worker.py](../python/gui_qt/workers/serial_worker.py).

The flow is:

- MainWindow creates a SerialHandler,
- MainWindow creates an AttendanceProcessor,
- MainWindow creates a SerialWorker and starts it in its own thread,
- the worker reads serial output in the background,
- the worker emits Qt signals for connection state, mode changes, scan events, raw lines, enroll progress, and wipe progress,
- MainWindow and page widgets consume those signals.

### 6.2 Thread lifecycle

The Qt worker is a `QThread` subclass. It uses:

- `run()` to loop until interrupted,
- `stop()` to set a flag and interrupt the thread,
- `quit()` and `wait()` in `MainWindow.closeEvent()`.

That is a common pattern, but it is vulnerable if the worker is still actively using the serial handler while shutdown begins.

### 6.3 Signal/slot ownership

The code uses signals such as `connection_changed`, `mode_changed`, `scan_event`, `raw_line`, `enroll_progress`, `wipe_progress`, and `error`. This is the right pattern for keeping the UI responsive.

### 6.4 UI-thread safety

The worker emits signals from its background thread, and the UI consumes them in the main thread. That is correct. However, the UI also directly calls `self.serial_handler.is_connected()` and sends commands from UI handlers. That can race with the worker’s read loop if the device disconnects or reconnects at the same time.

### 6.5 Window lifecycle and shutdown

The shutdown path in [python/gui_qt/main_window.py](../python/gui_qt/main_window.py) includes multiple steps:

- stop the worker,
- quit the worker,
- wait for the worker,
- disconnect the serial handler.

This is sensible, but it depends on the worker stopping cleanly. If the worker is hung in a blocking serial operation or in a reconnect loop, shutdown can still be delayed or inconsistent.

### 6.6 Why the Qt path is still fragile

The Qt path is newer and cleaner than the CustomTkinter path, but it still shares the same underlying serial and firmware assumptions. In other words, the UI layer does not cure the underlying instability; it mostly moves blocking work into a background thread.

---

## 7. Database

### 7.1 SQLite usage

The persistence layer is [python/core/database.py](../python/core/database.py). It uses SQLite with:

- `students` table for fingerprint IDs and student details,
- `attendance` table for scan output,
- indexes for student number, grade/section, and attendance lookups.

### 7.2 Connection creation

Every operation opens a new SQLite connection via `get_connection()`. The module also provides a `ManagedConnection` context manager that commits or rolls back on exit.

### 7.3 Transactions and commits

The code commits at the end of write operations. The `ManagedConnection` wrapper makes transaction handling more consistent, but there is still no explicit retry or recovery logic for lock contention.

### 7.4 Locking and concurrency

The module uses `sqlite3.connect(..., timeout=30)` which is explicitly tolerant of transient locking. That is positive, but the app also uses multiple short-lived connections, so the database can still become a bottleneck if scan events and GUI refreshes overlap.

### 7.5 Schema and migrations

The schema is created with `CREATE TABLE IF NOT EXISTS` and indexes. There is no migration system. That means schema evolution is minimal and somewhat fragile.

### 7.6 Attendance writes

Attendance writes happen from [python/core/attendance.py](../python/core/attendance.py) via `log_attendance()`. That is straightforward. The bigger issue is not database corruption; it is that the database writes are downstream of an unstable serial and scan parser pipeline.

### 7.7 Backups and restore

The database module includes backup and restore helpers. These are helpful but not central to the current instability.

### 7.8 Database corruption scenarios

The repository does not show evidence of catastrophic database corruption. The more realistic risk is data loss due to partial or repeated writes during reconnect or UI races, but the current code does not suggest a widespread corruption bug.

---

## 8. Logging

### 8.1 Logging architecture

The logging system is implemented in [python/core/logger.py](../python/core/logger.py). It wraps Python’s standard logging module and adds:

- structured payload support,
- custom formatting,
- rotating file logging,
- a logger proxy object for compatibility.

### 8.2 What is good

- logging is centralized,
- file and console handlers are configurable,
- structured fields are attached to log messages.

### 8.3 What is risky

The logging layer is not the root cause of the hardware issues, but it does have several weaknesses:

- log calls are used heavily in worker threads and reconnect paths,
- the logger supports a custom `success()` level, but the rest of the code uses `log.info()` and `log.error()` inconsistently,
- some code still passes strings to `log.error()` with interpolation, while other code passes structured kwargs, which can make logs harder to read and correlate,
- the logger is configured globally and may be reconfigured by different components in different contexts.

### 8.4 Logging issues visible in the repo

The code uses custom logging wrappers but also mixes them with standard `logging` imports. That is not fatal, but it is a sign of evolving abstractions.

---

## 9. LED System

The firmware’s LED behavior is implemented in the main sketch with a priority-based scheduler and several named states.

### 9.1 LED states present in code

The firmware supports the following LED states:

- `LED_BOOTING`
- `LED_READY`
- `LED_SCAN`
- `LED_SUCCESS`
- `LED_ENROLL`
- `LED_FIRMWARE`
- `LED_ERROR`
- `LED_DB_ERROR`
- `LED_COMMUNICATION_ERROR`
- `LED_HOST_CONNECTED`
- `LED_HOST_DISCONNECTED`
- `LED_SLEEP`

### 9.2 Trigger points

- Booting: `requestLedState(LED_BOOTING)` in `beginLedManager()`
- Ready: `ledReady()`
- Scan: `ledScan()`
- Enrollment: `ledEnroll()`
- Success: `ledSuccess()`
- Error: `ledError()`
- Firmware: `ledFirmware()`
- Host connected/disconnected: `ledHostConnected()` / `ledHostDisconnected()`
- Sleep: `ledSleep()`

### 9.3 Arbitration system

The LED manager assigns a priority value per state. Higher-priority states override lower-priority ones. This is a reasonable pattern, but it creates another state machine that must stay synchronized with the firmware’s command state.

### 9.4 Existing risks

The LED system is a likely contributor to confusing runtime behavior because:

- scan mode and enrollment mode both change the LED state,
- host connected/disconnected status can override or restore the previous state,
- temporary success/error states restore the previous state after a timeout,
- the code treats the LED manager as a general-purpose notification system, even though it is tied to the same hardware that is also running fingerprint logic.

---

## 10. Why There Are So Many Bugs

The repository does not suffer from one isolated bug. It shows several structural reasons why bugs accumulated.

### 10.1 Multiple competing implementations

The repository contains both a legacy CustomTkinter GUI and a newer Qt GUI, plus test scaffolds that duplicate those components. That produces inconsistent behaviors and keeps old code paths alive even when the new path is intended to replace them.

### 10.2 Firmware and Python evolved separately

The firmware emits text and JSON in ways that are only partially mirrored by the Python host. The host supports both, but the protocol is still effectively a compatibility patchwork rather than one canonical spec.

### 10.3 Repeated AI-assisted refactoring and documentation churn

The git history shows repeated feature additions and refactors: LED management, JSON handling, serial diagnostics, DB handling, GUI refactors, and documentation improvements. Each change appears to have been layered onto the previous implementation rather than replacing it cleanly.

### 10.4 Multiple state machines

The repository has several overlapping state machines:

- firmware command mode vs. scan mode,
- LED state manager,
- host connection/disconnection state,
- enrollment progress state,
- GUI scan toggle state.

These state machines are not unified, which creates race-like behavior.

### 10.5 Backward compatibility increased complexity

The code explicitly supports both legacy text outputs and newer JSON messages. That compatibility is useful, but it means the system has to preserve old behavior while simultaneously supporting new behavior. This makes the runtime more flexible but also more brittle.

### 10.6 Insufficient integration testing for hardware behavior

The tests focus on parsing and UI fragments but do not appear to exercise the full hardware path end to end. That means the repository can pass unit-style tests while still failing under real serial and fingerprint conditions.

---

## 11. Current Known Bugs

| Severity | Component | Bug | Evidence | Likely Cause | Impact |
| --- | --- | --- | --- | --- | --- |
| CRITICAL | Firmware / serial interaction | Repeated startup sequence during scan suggests the board is resetting or re-entering setup unexpectedly | Main firmware prints startup banner and `READY` in `setup()`; the user-reported sequence repeats during scan mode | Hardware reset, watchdog reset, crash, or unstable serial/boot path | Scan mode becomes unreliable and the host may lose state |
| HIGH | Serial protocol | Firmware and Python handle text and JSON differently across the same logical events | Firmware emits both text and JSON; Python parser accepts both; the Qt worker and legacy GUI parse differently | Lack of a single canonical protocol | Protocol mismatches create missed or duplicated events |
| HIGH | Reconnect logic | Reconnect loops can fire repeatedly when the device is unstable or the COM port is stale | [python/core/serial_handler.py](../python/core/serial_handler.py) schedules reconnects on failure and on disconnect | Background reconnect state is not fully coordinated with user actions | Reconnect churn and confusing UI behavior |
| HIGH | GUI / threading | UI and worker can race when device state changes during connect/disconnect or scan toggle | Main window and serial worker both manipulate connection and mode state | Background worker and UI both own state transitions | Spurious UI state changes or lost mode transitions |
| HIGH | Enrollment flow | Enrollment can be interrupted by new commands, but the firmware and host need to coordinate that carefully | `checkEnrollmentCancel()` in the firmware and dialog logic in [python/gui_qt/pages/students_page.py](../python/gui_qt/pages/students_page.py) | Enrollment uses a shared serial stream and a non-atomic state transition | Enrollment can be cancelled unexpectedly or leave the device in an inconsistent state |
| MEDIUM | Scan parsing | Attendance parsing depends on line ordering and timing and can inadvertently drop or misattribute scans | [python/core/attendance.py](../python/core/attendance.py) uses current ID + confidence pairs and cooldowns | Serial timing and firmware output ordering are not fully deterministic | Duplicate or missed attendance records |
| MEDIUM | LED state machine | LED state requests can conflict with each other and with firmware mode changes | LED manager uses priority-based restoration and multiple call sites in the firmware | Overlapping states and restore logic | Confusing device feedback and possible misinterpretation of status |
| MEDIUM | Logging | Logging is centralized but not fully structured or consistent across all paths | [python/core/logger.py](../python/core/logger.py) and multiple modules use different patterns | Log API evolved over time | Diagnostics are harder to correlate |
| LOW | Database | Database backup/restore and schema evolution are lightweight and not migration-aware | [python/core/database.py](../python/core/database.py) uses `CREATE TABLE IF NOT EXISTS` only | Schema changes will be awkward | Future maintenance risk |
| TECHNICAL DEBT | UI duplication | There are multiple GUI stacks and duplicate redesign folders | [python/gui](../python/gui), [python/gui_qt](../python/gui_qt), [tests/gui_qt_redesign](../tests/gui_qt_redesign) | Repeated implementation and migration work | Maintenance cost and inconsistent behaviors |

---

## 12. Suspected Scan Failure

The repository contains enough evidence to analyze the behavior described in the request: the ESP32 repeatedly prints its startup sequence while the user attempts a scan.

### Observed sequence from the firmware

The firmware prints this during startup in `setup()`:

- `Sensor found!`
- `Stored fingerprints: ...`
- `Commands...`
- `READY`
- `{"type":"status","state":"READY"}`

If those lines are observed repeatedly during runtime, the most likely interpretation is that the firmware is rebooting or re-entering `setup()`.

### Classification

#### CONFIRMED

- The repository clearly shows that the startup banner and `READY` output are emitted from the firmware’s `setup()` path.
- The firmware does not contain any explicit “reboot on SCAN” or “restart on scan failure” logic in the main sketch.

#### LIKELY

- A hardware reset, watchdog reset, or firmware crash is the most plausible explanation if the startup sequence repeats while scan mode is active.
- A serial disconnect/reconnect or host-side reconnect event could also expose the repeated startup output if the ESP32 is rebooting due to a power or timing issue.

#### POSSIBLE

- The firmware could be failing in a way that causes it to re-enter `setup()` after a sensor communication error or a loop failure.
- The host-side reconnect logic might be interacting with the device in a way that makes repeated startup output more visible, but the repository does not show the host explicitly resetting the ESP32.

#### UNKNOWN

- The repository does not contain a hardware log, a crash dump, or a captured serial trace from the user’s exact failing setup.
- The repository cannot prove whether the root cause is hardware, watchdog, power instability, a sensor failure, a serial timing issue, or a firmware crash without live hardware testing.

### Bottom line

The repository supports the conclusion that the repeated startup output is consistent with a device restart, not with a normal scan mode transition. It does not support a stronger claim than that without hardware evidence.

---

## 13. Error Timeline

The repository history and docs show a sequence of refactors and fixes that likely contributed to the current state.

### Timeline inferred from the repository

- Initial release: basic firmware + Python GUI + SQLite.
- A legacy CustomTkinter GUI was added and expanded.
- A newer Qt GUI path was introduced later.
- Serial handling and reconnect logic were refactored and improved multiple times.
- JSON status and attendance handling were added later.
- LED behavior was expanded and reworked.
- Logging and documentation were expanded substantially.
- The project now contains both new and old code paths that still influence one another.

### Why the timeline matters

The repository shows that newer changes were layered on top of older behavior rather than replacing it cleanly. This is why the project can appear to work in one mode and fail in another.

---

## 14. Dependency / Version Risks

### Python version

The repository targets a Python environment that includes PySide6 and pyserial. The current workspace has a Python 3.14 environment in the terminal context, while the project’s requirements list older versions. The repository does not show a strict pinning strategy for all environments beyond the requirements file.

### PySide6 / Qt

The Qt GUI depends on PySide6. The requirements file declares `PySide6>=6.5`, which is broad. That leaves room for behavior differences across installations.

### pyserial

The project depends on `pyserial==3.5`. That is a classic serial library and the code relies heavily on it. The serial port behavior is a major factor in the project’s reliability.

### ESP32 Arduino core

The firmware uses Arduino/ESP32 APIs and the Adafruit fingerprint library. The repository does not contain a pinned platform version or an explicit board package version. That introduces a compatibility risk for future updates.

### Adafruit fingerprint libraries

The firmware depends on Adafruit’s fingerprint library. The repository does not provide a pinned version for that dependency in the project docs or requirements. That is a risk because library behavior can change subtly across versions.

### esptool

The Python firmware helper uses `esptool` for flashing. The repository does not show a strict pinned version, and upload support appears optional.

### SQLite

SQLite is a strong fit for this project, but the code uses a very simple schema and no migration system. That is manageable but should be treated carefully as the project evolves.

---

## 15. Testing Gaps

### What is currently tested

The repository includes tests around:

- attendance parsing,
- auto-port probing,
- GUI startup/shutdown flows,
- some settings and theme behavior,
- database-related functions,
- basic import sanity.

Examples include:

- [tests/test_attendance_parsing.py](../tests/test_attendance_parsing.py)
- [tests/test_auto_port_probe.py](../tests/test_auto_port_probe.py)
- [tests/test_gui_shutdown.py](../tests/test_gui_shutdown.py)
- [tests/test_database_features.py](../tests/test_database_features.py)

### What is not meaningfully tested

The repository does not appear to have strong end-to-end tests for:

- firmware behavior on real hardware,
- serial communication during reconnect, disconnect, and device restart,
- scan mode transitions under load,
- fingerprint matching and confidence logic under real timing,
- Qt threading and shutdown under actual runtime conditions,
- database concurrency and lock behavior,
- JSON protocol compatibility across the two GUI paths,
- LED state machine interactions with host commands and scanning.

### Testing gap summary

The repository has unit-style and UI-adjacent tests, but not the kind of hardware-in-the-loop integration tests that this system actually needs.

---

## 16. Documentation Accuracy

### Documentation that appears broadly correct

- [docs/Architecture/architecture.md](../docs/Architecture/architecture.md) describes the broad system shape reasonably well.
- [docs/generated/SERIAL_PROTOCOL.md](../docs/generated/SERIAL_PROTOCOL.md) captures the existence of both text and JSON protocols.
- [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) correctly points to serial access issues as a common source of failure.

### Documentation that is outdated or incomplete

- The user-facing docs and generated docs appear to describe a project that is “modernized,” but the actual repository still contains multiple competing implementations.
- The docs do not fully reflect the fact that the codebase has both legacy and Qt GUI paths and duplicated redesign scaffolds.
- The docs often describe the intended architecture more cleanly than the current implementation does.

### Contradictory or misleading content

- The documentation often presents the project as if it were a single coherent architecture, but the repository clearly contains competing code paths and compatibility layers.
- The generated docs describe protocol support, but the actual firmware and Python host still behave differently in subtle ways depending on the path used.

---

## 17. Recommended Fix Order

This is a repair plan, not an implementation.

1. Critical stability problems
   - Address the repeated boot/startup loop and any hardware reset path first.
   - This is the most important because the rest of the system depends on the device staying alive.

2. Firmware crashes / resets
   - Investigate what causes the firmware to re-enter setup or fail at runtime.
   - This should be treated as a root-cause investigation before changing the host or UI.

3. Serial protocol problems
   - Normalize the protocol around one canonical format or maintain a strict and tested compatibility layer.
   - Fix mismatches between legacy text and JSON semantics.

4. Threading and lifecycle problems
   - Make connect/disconnect, worker shutdown, and reconnect state transitions deterministic.
   - The current background worker design is useful but must be made more robust.

5. State-machine problems
   - Unify command mode, scan mode, enrollment, and LED state management into a simpler architecture.

6. Database problems
   - Keep the database layer simple, but ensure writes are resilient and the schema is migration-aware.

7. Logging
   - Improve structured logging and correlation of firmware, serial, and GUI events.

8. Testing
   - Add integration tests that cover real serial behavior and reconnect behavior.

9. Documentation

- Update docs to reflect the actual architecture and current protocol behavior.

1. Cleanup / refactoring

- Remove or archive duplicate GUI and prototype code once the runtime path is stable.

This order is appropriate because the most damaging issues are upstream of everything else: device stability and protocol semantics.

---

## 18. “DO NOT TOUCH YET” Section

The following should not be changed until the underlying problem is understood:

- The main firmware sketch in [firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino](../firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino)
  - It is central to the suspected reset path and the serial protocol behavior.
- The serial protocol handling in [python/core/serial_handler.py](../python/core/serial_handler.py) and [python/core/device_discovery.py](../python/core/device_discovery.py)
  - These are the current compatibility boundary between firmware and host.
- The LED manager inside the firmware sketch
  - It is intertwined with mode changes and could hide the real root cause if changed prematurely.
- The Qt worker and main window lifecycle in [python/gui_qt/workers/serial_worker.py](../python/gui_qt/workers/serial_worker.py) and [python/gui_qt/main_window.py](../python/gui_qt/main_window.py)
  - These are important, but they are downstream of the device stability and protocol issues.
- The database schema in [python/core/database.py](../python/core/database.py)
  - Database changes should not be the first response to a serial/firmware failure.

---

## 19. File-by-File Inventory

| File | Purpose | Important Functions / Classes | Dependencies | Risk | Status |
| --- | --- | --- | --- | --- | --- |
| [firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino](../firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino) | Main firmware sketch | `setup()`, `loop()`, `handleCommand()`, `enrollFinger()`, `scanFinger()`, LED state helpers | Adafruit fingerprint library, HardwareSerial | Critical | Active core implementation |
| [firmware/attendance/attendance.ino](../firmware/attendance/attendance.ino) | Simple attendance sketch | Basic scan loop | Same fingerprint library | Medium | Legacy/auxiliary |
| [firmware/enroll/enroll.ino](../firmware/enroll/enroll.ino) | Enrollment sketch | Enrollment flow | Same fingerprint library | Medium | Legacy/auxiliary |
| [firmware/delete/delete.ino](../firmware/delete/delete.ino) | Delete utility | Delete/wipe operations | Same fingerprint library | Medium | Legacy/auxiliary |
| [python/core/serial_handler.py](../python/core/serial_handler.py) | Serial boundary | `SerialHandler`, `connect()`, `disconnect()`, `send_command()`, `read_line()`, reconnect worker | pyserial, device discovery, logging | High | Active |
| [python/core/device_discovery.py](../python/core/device_discovery.py) | Discovery and handshake | `discover_device()`, `_probe_port()`, `_validate_handshake()` | pyserial, logging | High | Active |
| [python/core/attendance.py](../python/core/attendance.py) | Attendance parsing and logging | `AttendanceProcessor`, `process_line()` | Database, config, logger | High | Active |
| [python/core/database.py](../python/core/database.py) | SQLite persistence | `init_database()`, `log_attendance()`, `backup_database()`, `restore_database()` | sqlite3, matplotlib | Medium | Active |
| [python/core/commands.py](../python/core/commands.py) | High-level command wrappers | `cmd_scan()`, `cmd_stop()`, `cmd_enroll()`, `cmd_delete()`, `cmd_wipe()` | Serial handler | Medium | Active |
| [python/core/logger.py](../python/core/logger.py) | Logging abstraction | `AppFormatter`, `LOG`, `log` proxy | standard logging | Medium | Active |
| [python/core/firmware_helper.py](../python/core/firmware_helper.py) | Firmware upload helpers | `upload_firmware_with_progress()` | esptool, subprocess | Medium | Active |
| [python/gui_qt/main_window.py](../python/gui_qt/main_window.py) | Qt main window | `MainWindow`, signal handlers, close lifecycle | Qt widgets, serial worker | High | Active |
| [python/gui_qt/workers/serial_worker.py](../python/gui_qt/workers/serial_worker.py) | Background serial worker | `SerialWorker`, parsing helpers | Qt signals, attendance processor | High | Active |
| [python/gui_qt/pages/students_page.py](../python/gui_qt/pages/students_page.py) | Enrollment and wipe UI | `EnrollDialog`, `WipeDialog`, `StudentsPage` | Qt widgets, student service | Medium | Active |
| [python/gui/app.py](../python/gui/app.py) | Legacy CustomTkinter app | `FingerprintApp` | customtkinter, serial handler | High | Legacy |
| [python/config.py](../python/config.py) | Runtime config | `AppConfig`, `get_config()` | environment variables | Medium | Active |
| [python/settings_store.py](../python/settings_store.py) | Settings persistence | `load_settings()`, `save_settings()`, `cleanup_stale_port()` | JSON | Medium | Active |
| [python/main.py](../python/main.py) | Console entry point | `input_thread()`, `main()` | serial handler, attendance processor | Medium | Legacy / compatibility |
| [requirements.txt](../requirements.txt) | Dependency list | — | pyserial, PySide6, customtkinter, pytest | Medium | Active |
| [README.md](../README.md) | Project overview | — | — | Low | Partially accurate |
| [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) | Troubleshooting | — | — | Medium | Useful but not a full root-cause guide |
| [tests/test_attendance_parsing.py](../tests/test_attendance_parsing.py) | Attendance parsing regression | `AttendanceParsingTest` | unittest | Medium | Partial |
| [tests/test_auto_port_probe.py](../tests/test_auto_port_probe.py) | Port probing smoke tests | `test_common_port_candidates_include_common_values()` | unittest | Medium | Partial |
| [tests/test_gui_shutdown.py](../tests/test_gui_shutdown.py) | GUI shutdown behavior | `GuiShutdownTest` | unittest | Medium | Partial |

---

## 20. Final Diagnosis

What is actually wrong with this project right now?

The project is not simply “bad code.” It is a system whose core path is unstable because the firmware, Python host, and GUI were built and evolved in parallel, while each layer preserved compatibility with older behavior. The result is a runtime that can appear to work in simple scenarios but fails in real-world scenarios involving reconnects, scan mode transitions, enrollment interrupts, and hardware timing.

The most important architectural condition is this:

- the firmware has a real state machine, but it is not fully unified with the host-side protocol expectations,
- the host has a serial boundary and a worker thread, but the reconnection and mode changes are not fully coordinated with the device state,
- the GUI has multiple implementations and the system still carries legacy compatibility layers,
- the protocol is effectively a hybrid of text and JSON, which creates a recurring source of fragility.

That is why the project can seem functional in one situation and fail in another. The code is not just “messy”; it is split across overlapping abstractions that are only loosely synchronized. The main repair task is not to “clean up the code” first. It is to stabilize the device/host contract and then simplify the layers around it.

---

## Audit Statistics

- Files scanned: 4,200
- Firmware files: 6
- Python files: 1,519
- Test files: 77
- Documentation files: 42
- Major components: 12+
- Confirmed bugs: 4+
- Likely bugs: 6+
- Technical debt items: 6+
- Critical issues: 1
- High issues: 4
- Medium issues: 4
- Low issues: 1
