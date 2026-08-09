"""
SerialWorker
------------
Wraps your existing `serial_handler.py` in a QThread so ESP32 I/O never
blocks the UI. This is the main reason PySide6 is a good fit here: Qt's
signal/slot system is thread-safe by design, so pushing a scan event from
this background thread into a table widget on the main thread is safe
without manual locking.

ASSUMPTIONS (adjust to match your actual serial_handler.py / commands.py
interfaces — these are based on the architecture doc, not the real code):
  - serial_handler.connect(port, baud) -> bool
  - serial_handler.read_line() -> str | None   (non-blocking or short timeout)
  - commands.send(command_name, **kwargs)
  - attendance.parse_message(line) -> dict | None
      e.g. {"type": "scan", "student_id": ..., "confidence": ..., "status": ...}

If your real modules differ, only this file and the two TODOs below need
to change — the rest of the UI just listens to signals.
"""

from PySide6.QtCore import QThread, Signal
import time

# TODO: point these at your real backend modules
# from core import serial_handler, commands, attendance


class SerialWorker(QThread):
    connection_changed = Signal(str)          # "connected" | "disconnected" | "connecting"
    scan_event = Signal(dict)                 # raw parsed attendance event
    log_line = Signal(str)                    # raw line, useful for the Logs page
    error = Signal(str)

    def __init__(self, port: str, baud: int, parent=None):
        super().__init__(parent)
        self.port = port
        self.baud = baud
        self._running = False
        self._reconnect_delay = 2.0

    def run(self):
        self._running = True
        while self._running:
            self.connection_changed.emit("connecting")
            try:
                # TODO: replace with serial_handler.connect(self.port, self.baud)
                connected = self._connect_stub()
            except Exception as exc:
                self.error.emit(f"Connection failed: {exc}")
                connected = False

            if not connected:
                time.sleep(self._reconnect_delay)
                continue

            self.connection_changed.emit("connected")
            self._read_loop()
            self.connection_changed.emit("disconnected")
            if self._running:
                time.sleep(self._reconnect_delay)

    def _read_loop(self):
        while self._running:
            try:
                # TODO: replace with serial_handler.read_line()
                line = self._read_line_stub()
            except Exception as exc:
                self.error.emit(f"Read error: {exc}")
                return  # drop out, outer loop will reconnect

            if line is None:
                continue

            self.log_line.emit(line)

            # TODO: replace with attendance.parse_message(line)
            event = self._parse_stub(line)
            if event:
                self.scan_event.emit(event)

    def stop(self):
        self._running = False
        self.wait(2000)

    # ---- stubs to remove once wired to real backend ----
    def _connect_stub(self):
        return True

    def _read_line_stub(self):
        time.sleep(0.5)
        return None

    def _parse_stub(self, line):
        return None
