"""Worker thread for non-blocking serial connection operations."""

import threading
from typing import Optional

from PySide6.QtCore import QThread, Signal

from core.serial_handler import SerialHandler
from core.logger import log


class ConnectionWorker(QThread):
    """Background worker for serial connect/disconnect operations."""
    
    # Signals emitted back to main window
    connect_result = Signal(bool, str)  # (success, message)
    connection_state_changed = Signal(str)  # "connecting" | "connected" | "disconnected"

    def __init__(self, serial_handler: SerialHandler):
        super().__init__()
        self.serial_handler = serial_handler
        self._pending_operation = None
        self._operation_lock = threading.RLock()

    def connect_to_device(self, port: str, baud: int, auto_detect: bool = False):
        """Queue a connection operation to run in the background."""
        with self._operation_lock:
            self._pending_operation = ("connect", port, baud, auto_detect)

    def disconnect_from_device(self):
        """Queue a disconnection operation to run in the background."""
        with self._operation_lock:
            self._pending_operation = ("disconnect",)

    def run(self):
        log.info(
            "ConnectionWorker.run() entered",
            thread_id=threading.get_ident(),
            thread_name=threading.current_thread().name,
        )

        while not self.isInterruptionRequested():
            with self._operation_lock:
                operation = self._pending_operation
                self._pending_operation = None

            if operation is None:
                self.msleep(100)
                continue

            try:
                if operation[0] == "connect":
                    _, port, baud, auto_detect = operation
                    log.info("ConnectionWorker: starting connect", port=port, baud=baud, auto_detect=auto_detect)
                    self.connection_state_changed.emit("connecting")
                    ok, msg = self.serial_handler.connect(port, baud, auto_detect=auto_detect)
                    if ok:
                        log.info("ConnectionWorker: connect succeeded", port=port)
                        self.connection_state_changed.emit("connected")
                    else:
                        log.warning("ConnectionWorker: connect failed", error=msg)
                        self.connection_state_changed.emit("disconnected")
                    self.connect_result.emit(ok, msg)

                elif operation[0] == "disconnect":
                    log.info("ConnectionWorker: starting disconnect")
                    self.connection_state_changed.emit("disconnected")
                    self.serial_handler.disconnect()
                    log.info("ConnectionWorker: disconnect complete")
                    self.connect_result.emit(True, "Disconnected")
            except Exception as exc:
                log.exception(
                    "Exception in ConnectionWorker operation",
                    operation_type=operation[0] if operation else "unknown",
                    error=str(exc),
                )
                if operation and operation[0] == "connect":
                    self.connection_state_changed.emit("disconnected")
                    self.connect_result.emit(False, f"Exception during connect: {str(exc)}")

        log.info(
            "ConnectionWorker.run() exiting",
            thread_id=threading.get_ident(),
            thread_name=threading.current_thread().name,
        )

    def stop(self):
        """Stop the worker thread gracefully."""
        self.requestInterruption()
        self.quit()
        self.wait(2000)
