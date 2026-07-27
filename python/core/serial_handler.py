"""Serial communication boundary for the ESP32 fingerprint device.

This module owns port discovery, connection setup, read/write operations, and
reconnect behavior so the rest of the application can stay focused on higher
level workflow logic.
"""

###############################################################################
#  serial_handler.py
#  AS608 Fingerprint Attendance System
#
#  All ESP32 serial communication lives here.
#  No database code, no business logic — just read and send.
###############################################################################

import time
import threading
from typing import Optional, List, Tuple

try:
    import serial
    from serial.tools import list_ports
except ModuleNotFoundError:  # pragma: no cover
    serial = None
    list_ports = None

from config import get_config
from core.logger import log

CONFIG = get_config()

RECONNECT_MAX_DELAY = 30


def list_serial_ports() -> List[str]:
    """Return a list of available serial port names."""
    if serial is None or list_ports is None:
        return []
    try:
        return [port.device for port in list_ports.comports()]
    except Exception:
        return []


class SerialHandler:
    def __init__(self) -> None:
        self.esp32: Optional[object] = None
        self.connected = False
        self.reconnect_count = 0
        self.reconnect_port: Optional[str] = None
        self.reconnect_baud: Optional[int] = None
        self.auto_reconnect_enabled = CONFIG.auto_reconnect
        self._pyserial_missing_warning_shown = False
        self._lock = threading.RLock()
        self._reconnect_thread: Optional[threading.Thread] = None
        self._reconnect_stop = threading.Event()

    @property
    def pyserial_installed(self) -> bool:
        return serial is not None

    def list_available_ports(self) -> List[str]:
        return list_serial_ports()

    def connect(self, port: str = "", baud: int = 115200, wait_for_device: bool = False) -> Tuple[bool, str]:
        """
        Connect to ESP32 over serial.
        Returns (True, "OK") or (False, error message).
        """
        if serial is None:
            self.connected = False
            if not self._pyserial_missing_warning_shown:
                log.error("pyserial not installed", error="pyserial missing")
                self._pyserial_missing_warning_shown = True
            return False, "pyserial is not installed. Run: pip install -r requirements.txt"

        port = port or CONFIG.com_port
        baud = baud or CONFIG.baud_rate
        self.reconnect_port = port
        self.reconnect_baud = baud
        self._reconnect_stop.clear()

        with self._lock:
            if self.esp32 is not None and getattr(self.esp32, "is_open", False):
                try:
                    self.esp32.close()
                except Exception:
                    pass
                self.esp32 = None

            try:
                self.esp32 = serial.Serial(port, baud, timeout=0)
                if wait_for_device:
                    time.sleep(2)
                self.connected = True
                self.reconnect_count = 0
                log.success("Connected to ESP32", port=port, baud=baud)
                return True, "OK"
            except Exception as exc:
                self.connected = False
                self.esp32 = None
                log.error("Serial connection failed", port=port, baud=baud, error=str(exc))
                if self.auto_reconnect_enabled:
                    self._schedule_reconnect()
                return False, str(exc)

    def disconnect(self) -> None:
        """Close serial connection cleanly and stop reconnect attempts."""
        with self._lock:
            self._reconnect_stop.set()
            self._join_reconnect_thread()

            if self.esp32 is not None and getattr(self.esp32, "is_open", False):
                try:
                    self.esp32.write(("STOP\n").encode("utf-8"))
                except Exception:
                    pass
                try:
                    self.esp32.close()
                except Exception:
                    pass
            self.esp32 = None
            self.connected = False

        log.info("Disconnected from ESP32", port=self.reconnect_port, baud=self.reconnect_baud)

    def send_command(self, cmd: str) -> bool:
        """
        Send a command string to the ESP32.
        Commands are uppercased automatically.
        Returns True if sent, False if not connected or on failure.
        """
        with self._lock:
            if not self.is_connected():
                return False
            try:
                self.esp32.write((cmd.strip().upper() + "\n").encode("utf-8"))
                return True
            except Exception as exc:
                log.error("Failed to send command to ESP32", command=cmd.strip().upper(), error=str(exc))
                self.connected = False
                self._schedule_reconnect()
                return False

    def read_line(self) -> Optional[str]:
        """
        Read a single line from ESP32.
        Returns decoded text or None if no complete line is available.
        """
        with self._lock:
            if not self.is_connected():
                if self.auto_reconnect_enabled and self.reconnect_port:
                    self._schedule_reconnect()
                return None

            if self.esp32.in_waiting == 0:
                return None

            try:
                raw = self.esp32.readline()
            except Exception as exc:
                log.error("Serial read error", error=str(exc))
                self.connected = False
                self._schedule_reconnect()
                return None

        try:
            return raw.decode("utf-8", errors="ignore").strip()
        except Exception:
            return None

    def should_ignore(self, line: str) -> bool:
        """Returns True for boot noise and ESP32 help text."""
        for prefix in CONFIG.ignore_prefixes:
            if line.startswith(prefix):
                return True
        return False

    def is_connected(self) -> bool:
        with self._lock:
            return bool(self.connected and self.esp32 is not None and getattr(self.esp32, "is_open", False))

    def auto_reconnect(self) -> bool:
        """
        Trigger a background reconnect attempt.
        Returns True when a reconnect worker is already running or scheduled.
        """
        if not self.auto_reconnect_enabled or not self.reconnect_port:
            return False
        self._schedule_reconnect()
        return True

    def _schedule_reconnect(self) -> None:
        with self._lock:
            if not self.auto_reconnect_enabled or not self.reconnect_port:
                return

            if self._reconnect_thread is not None and self._reconnect_thread.is_alive():
                return

            self._reconnect_stop.clear()
            self._reconnect_thread = threading.Thread(target=self._reconnect_worker, daemon=True)
            self._reconnect_thread.start()

    def _join_reconnect_thread(self) -> None:
        thread = self._reconnect_thread
        if thread is None:
            return
        if thread.is_alive():
            thread.join(timeout=1.0)
        self._reconnect_thread = None

    def _reconnect_worker(self) -> None:
        while not self._reconnect_stop.is_set() and self.reconnect_count < CONFIG.reconnect_max_retries:
            delay = min(CONFIG.reconnect_base_delay * (2 ** self.reconnect_count), RECONNECT_MAX_DELAY)
            self.reconnect_count += 1
            log.warning(
                "Attempting reconnect",
                attempt=self.reconnect_count,
                max_attempts=CONFIG.reconnect_max_retries,
                delay_seconds=delay,
                port=self.reconnect_port,
                baud=self.reconnect_baud,
            )

            if self._reconnect_stop.wait(delay):
                return

            with self._lock:
                if self._reconnect_stop.is_set():
                    return
                success, msg = self._attempt_connect(self.reconnect_port, self.reconnect_baud)

            if success:
                log.success("Auto-reconnect successful", port=self.reconnect_port, baud=self.reconnect_baud)
                return

            log.warning(
                "Auto-reconnect attempt failed",
                attempt=self.reconnect_count,
                max_attempts=CONFIG.reconnect_max_retries,
                reason=msg,
            )

        if not self.is_connected():
            log.error(
                "Auto-reconnect failed",
                attempts=self.reconnect_count,
                max_attempts=CONFIG.reconnect_max_retries,
            )

    def _attempt_connect(self, port: Optional[str], baud: Optional[int]) -> Tuple[bool, str]:
        if serial is None or port is None or baud is None:
            return False, "serial unavailable"

        try:
            if self.esp32 is not None and getattr(self.esp32, "is_open", False):
                self.esp32.close()
            self.esp32 = serial.Serial(port, baud, timeout=0)
            self.connected = True
            return True, "OK"
        except Exception as exc:
            self.connected = False
            self.esp32 = None
            return False, str(exc)
