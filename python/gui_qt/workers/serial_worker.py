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
import threading
import time
from datetime import datetime
from typing import Optional

from PySide6.QtCore import QThread, Signal

from core.serial_handler import SerialHandler
from core.attendance import AttendanceProcessor
from core.logger import log
from core.utils import parse_json_line

RE_ENROLLING_AS = re.compile(r"ENROLLING FINGER AS ID #(\d+)", re.IGNORECASE)
RE_ENROLL_SUCCESS = re.compile(r"SUCCESS!?\s*Finger saved as ID #(\d+)", re.IGNORECASE)
RE_ENROLL_CANCEL = re.compile(r"ENROLLMENT cancelled|Enrollment cancelled|ENROLL_CANCELLED", re.IGNORECASE)
RE_WIPE_START = re.compile(r"Wiping ALL fingerprints", re.IGNORECASE)
RE_WIPE_SUCCESS = re.compile(r"SUCCESS\s*-\s*All fingerprints deleted", re.IGNORECASE)
RE_STORED_COUNT = re.compile(r"Stored fingerprints:\s*(\d+)", re.IGNORECASE)


class SerialWorker(QThread):
    connection_changed = Signal(str)   # "connected" | "disconnected" | "connecting"
    mode_changed = Signal(str)         # "scan" | "command"
    scan_event = Signal(dict)          # processed + student-joined scan result
    raw_line = Signal(str)             # raw ESP32 serial output for diagnostics
    enroll_progress = Signal(dict)     # {"event": "enrolling"|"success"|"cancelled"|"error", "id": str|None}
    wipe_progress = Signal(dict)       # {"event": "start"|"success"|"error"}
    fingerprint_count = Signal(int)    # response to the LIST command
    error = Signal(str)

    def __init__(self, serial_handler: SerialHandler, attendance_processor: AttendanceProcessor, parent: Optional[object] = None):
        super().__init__(parent)
        self.serial_handler = serial_handler
        self.attendance_processor = attendance_processor
        self._running = False
        self._last_connected_state = None
        self._last_reconnect_count = 0
        self._pending_enroll_status = None
        self._last_heartbeat_log = 0.0
        self._lines_since_heartbeat = 0

    def run(self):
        log.info(
            "SerialWorker.run() entered",
            thread_id=threading.get_ident(),
            thread_name=threading.current_thread().name,
        )
        self._running = True
        while self._running and not self.isInterruptionRequested():
            try:
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

                # Rate-limited proof-of-life: if the "monitor doesn't update"
                # symptom happens again, this tells us within seconds whether
                # this thread is actually alive and iterating at all, versus
                # stuck/blocked somewhere - which the Application Log entries
                # alone couldn't distinguish before.
                now = time.time()
                if now - self._last_heartbeat_log > 5.0:
                    log.debug(
                        "SerialWorker heartbeat: loop alive",
                        lines_emitted_since_last_heartbeat=self._lines_since_heartbeat,
                        thread_id=threading.get_ident(),
                    )
                    self._last_heartbeat_log = now
                    self._lines_since_heartbeat = 0

                try:
                    line = self.serial_handler.read_line()
                except Exception as exc:
                    self.error.emit(str(exc))
                    time.sleep(0.2)
                    continue

                if not line:
                    time.sleep(0.05)
                    continue

                self._lines_since_heartbeat += 1
                self.raw_line.emit(line)
                if self.serial_handler.should_ignore(line):
                    continue

                self._parse_mode_line(line)
                self._process_line(line)
                self._parse_enroll_progress(line)
                self._parse_wipe_progress(line)
                self._parse_fingerprint_count(line)
            except Exception as exc:
                self.error.emit(str(exc))
                log.exception(
                    "Unexpected exception in serial worker",
                    error=str(exc),
                    thread_id=threading.get_ident(),
                    thread_name=threading.current_thread().name,
                )
                time.sleep(0.2)

        log.info(
            "SerialWorker.run() exiting",
            thread_id=threading.get_ident(),
            thread_name=threading.current_thread().name,
        )

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
        """Mirrors app.py's _dispatch_attendance_message / _handle_scan_result.

        Cooldown-skipped (duplicate) scans are NOT written to the attendance
        database (that's still correct - we don't want double time-in rows),
        but they ARE still emitted as a scan_event so the UI can show the
        operator that a scan was received and why it wasn't logged, instead
        of it looking like nothing happened at all.
        """
        result = self.attendance_processor.process_line(line)
        if result is None:
            return

        logged = bool(result.get("logged"))
        fingerprint_id = int(result.get("fingerprint_id", 0) or 0)
        confidence = int(result.get("confidence", 0) or 0)
        raw_status = result.get("status") or "UNKNOWN"
        timestamp = result.get("timestamp") or datetime.now()

        student = None
        if fingerprint_id != 0:
            student = self.attendance_processor.lookup_student(fingerprint_id)

        if logged:
            status = "UNKNOWN" if fingerprint_id == 0 else "Present"
        else:
            status = "Duplicate"

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
            "status": status,
            "raw_status": raw_status,
            "logged": logged,
            "cooldown_reason": result.get("reason") if not logged else None,
        }
        self.scan_event.emit(event)

    def _parse_enroll_progress(self, message: str):
        """Mirrors app.py's _parse_enroll_progress — emitted regardless of whether
        an enroll dialog is open; the dialog decides whether it cares."""
        message = message.strip()
        if not message:
            return

        match = RE_ENROLLING_AS.search(message)
        if match:
            enrollment_id = match.group(1)
            log.debug(f"SerialWorker: Enrollment started with ID {enrollment_id}", raw_message=message)
            self.enroll_progress.emit({"event": "enrolling", "id": enrollment_id})
            return

        match = RE_ENROLL_SUCCESS.search(message)
        if match:
            enrollment_id = match.group(1)
            log.debug(f"SerialWorker: Enrollment succeeded for ID {enrollment_id}", raw_message=message)
            self.enroll_progress.emit({"event": "success", "id": enrollment_id})
            return

        if RE_ENROLL_CANCEL.search(message):
            log.debug("SerialWorker: Enrollment cancelled", raw_message=message)
            self.enroll_progress.emit({"event": "cancelled", "id": None})
            return

        upper = message.upper()
        if "ERROR" in upper or "FAIL" in upper:
            log.debug("SerialWorker: Enrollment error detected", raw_message=message)
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

    def _parse_fingerprint_count(self, line: str):
        """Response to the LIST command (also printed once at boot):
        '>> Stored fingerprints: N' or 'Stored fingerprints: N'."""
        match = RE_STORED_COUNT.search(line)
        if match:
            self.fingerprint_count.emit(int(match.group(1)))

    def stop(self):
        self._running = False
        self.requestInterruption()
        self.quit()
        self.wait(2000)