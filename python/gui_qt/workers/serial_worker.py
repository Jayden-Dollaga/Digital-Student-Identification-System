"""
SerialWorker
------------
Wraps the real `core.serial_handler.SerialHandler` in a QThread so ESP32
I/O never blocks the UI. Ports the exact flow from gui/app.py:
  read_serial_output() -> log_message() -> _append_log_message() ->
  _parse_connection_mode() / _dispatch_attendance_message() /
  _parse_enroll_progress() / _parse_wipe_progress()
to Qt signals instead of Tkinter's `self.after(0, ...)`.

Regexes are copied verbatim from gui/app.py so enroll/wipe dialog
behavior matches exactly.
"""

import re
import time
from datetime import datetime

from PySide6.QtCore import QThread, Signal

from core.serial_handler import SerialHandler
from core.attendance import AttendanceProcessor
from core.utils import parse_json_line

RE_ENROLLING_AS = re.compile(r"ENROLLING FINGER AS ID #(\d+)", re.IGNORECASE)
RE_ENROLL_SUCCESS = re.compile(r"SUCCESS!?\s*Finger saved as ID #(\d+)", re.IGNORECASE)
RE_ENROLL_CANCEL = re.compile(r"ENROLLMENT cancelled|Enrollment cancelled|ENROLL_CANCELLED", re.IGNORECASE)
RE_WIPE_START = re.compile(r"Wiping ALL fingerprints", re.IGNORECASE)
RE_WIPE_SUCCESS = re.compile(r"SUCCESS\s*-\s*All fingerprints deleted", re.IGNORECASE)


class SerialWorker(QThread):
    connection_changed = Signal(str)   # "connected" | "disconnected" | "connecting"
    mode_changed = Signal(str)         # "scan" | "command"
    scan_event = Signal(dict)          # processed + student-joined scan result
    log_line = Signal(str)             # raw ESP32 line, for the Logs page
    enroll_progress = Signal(dict)     # {"event": "enrolling"|"success"|"cancelled"|"error", "id": str|None}
    wipe_progress = Signal(dict)       # {"event": "start"|"success"|"error"}
    error = Signal(str)

    def __init__(self, serial_handler: SerialHandler, attendance_processor: AttendanceProcessor, parent=None):
        super().__init__(parent)
        self.serial_handler = serial_handler
        self.attendance_processor = attendance_processor
        self._running = False
        self._last_connected_state = None
        self._last_reconnect_count = 0

    def run(self):
        self._running = True
        while self._running and not self.isInterruptionRequested():
            connected = self.serial_handler.is_connected()

            if connected != self._last_connected_state:
                self._last_connected_state = connected
                self.connection_changed.emit("connected" if connected else "disconnected")

            if not connected:
                if self.serial_handler.reconnect_count != self._last_reconnect_count:
                    self._last_reconnect_count = self.serial_handler.reconnect_count
                    if self.serial_handler.reconnect_count > 0:
                        self.connection_changed.emit("connecting")
                time.sleep(0.2)
                continue

            self._last_reconnect_count = 0

            try:
                line = self.serial_handler.read_line()
            except Exception as exc:
                self.error.emit(str(exc))
                time.sleep(0.2)
                continue

            if not line:
                time.sleep(0.05)
                continue

            if self.serial_handler.should_ignore(line):
                continue

            self.log_line.emit(f"ESP32: {line}")
            self._parse_mode_line(line)
            self._process_line(line)
            self._parse_enroll_progress(line)
            self._parse_wipe_progress(line)

    def _parse_mode_line(self, line: str):
        parsed = parse_json_line(line)
        if parsed is not None and parsed.get("type") == "status":
            state = parsed.get("state")
            if state == "SCAN_MODE":
                self.mode_changed.emit("scan")
                return
            if state == "CMD_MODE":
                self.mode_changed.emit("command")
                return

        if line == "SCAN_MODE":
            self.mode_changed.emit("scan")
        elif line == "CMD_MODE":
            self.mode_changed.emit("command")

    def _process_line(self, line: str):
        """Mirrors app.py's _dispatch_attendance_message / _handle_scan_result."""
        result = self.attendance_processor.process_line(line)
        if result is None or not result.get("logged"):
            return

        fingerprint_id = int(result.get("fingerprint_id", 0) or 0)
        confidence = int(result.get("confidence", 0) or 0)
        raw_status = result.get("status") or "UNKNOWN"
        timestamp = result.get("timestamp") or datetime.now()

        student = None
        if fingerprint_id != 0:
            student = self.attendance_processor.lookup_student(fingerprint_id)

        event = {
            "fingerprint_id": fingerprint_id,
            "student_no": student.get("student_no") if student else "N/A",
            "student_name": (student.get("student_name") if student
                              else ("Unknown fingerprint" if fingerprint_id else "Unregistered")),
            "grade": student.get("grade") if student else "N/A",
            "section": student.get("section") if student else "N/A",
            "date": timestamp.strftime("%Y-%m-%d"),
            "time": timestamp.strftime("%H:%M:%S"),
            "confidence": confidence,
            "status": "UNKNOWN" if fingerprint_id == 0 else "Present",
            "raw_status": raw_status,
        }
        self.scan_event.emit(event)

    def _parse_enroll_progress(self, message: str):
        """Mirrors app.py's _parse_enroll_progress — emitted regardless of whether
        an enroll dialog is open; the dialog decides whether it cares."""
        match = RE_ENROLLING_AS.search(message)
        if match:
            self.enroll_progress.emit({"event": "enrolling", "id": match.group(1)})
            return

        match = RE_ENROLL_SUCCESS.search(message)
        if match:
            self.enroll_progress.emit({"event": "success", "id": match.group(1)})
            return

        if RE_ENROLL_CANCEL.search(message):
            self.enroll_progress.emit({"event": "cancelled", "id": None})
            return

        upper = message.upper()
        if "ERROR" in upper or "FAIL" in upper:
            self.enroll_progress.emit({"event": "error", "id": None})

    def _parse_wipe_progress(self, message: str):
        """Mirrors app.py's _parse_wipe_progress."""
        if RE_WIPE_START.search(message):
            self.wipe_progress.emit({"event": "start"})
            return

        if RE_WIPE_SUCCESS.search(message):
            self.wipe_progress.emit({"event": "success"})
            return

        upper = message.upper()
        if "ERROR" in upper or "FAIL" in upper:
            self.wipe_progress.emit({"event": "error"})

    def stop(self):
        self._running = False
        self.requestInterruption()
        self.quit()
        self.wait(2000)
