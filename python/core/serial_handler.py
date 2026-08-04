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
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    import serial
    from serial.tools import list_ports
except ModuleNotFoundError:  # pragma: no cover
    serial = None
    list_ports = None

from config import get_config, get_default_com_port
from core.device_discovery import discover_device
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


def build_common_port_candidates(existing_ports: Optional[List[str]] = None) -> List[str]:
    """Return a list of common COM ports to try, with detected ports last."""
    ports = list(existing_ports or list_serial_ports())
    seen: Set[str] = set()
    ordered: List[str] = []
    common = [
        "COM1", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "COM10", "COM11", "COM12",
    ]
    for port in common:
        if port not in seen:
            seen.add(port)
            ordered.append(port)
    for port in ports:
        if port not in seen:
            seen.add(port)
            ordered.append(port)
    return ordered


class SerialHandler:
    def __init__(self) -> None:
        self.esp32: Any = None
        self.connected = False
        self.reconnect_count = 0
        self.reconnect_port: Optional[str] = None
        self.reconnect_baud: Optional[int] = None
        self.device_metadata: Optional[Dict[str, Any]] = None
        self.auto_reconnect_enabled = CONFIG.auto_reconnect
        self._pyserial_missing_warning_shown = False
        self._lock = threading.RLock()
        self._reconnect_thread: Optional[threading.Thread] = None
        self._reconnect_stop = threading.Event()
        self._read_buffer = b""

    @property
    def pyserial_installed(self) -> bool:
        return serial is not None

    def list_available_ports(self) -> List[str]:
        return list_serial_ports()

    def connect(
        self,
        port: str = "",
        baud: int = 115200,
        wait_for_device: bool = False,
        auto_detect: bool = False,
    ) -> Tuple[bool, str]:
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

        port = port.strip() if port else ""
        baud = baud or CONFIG.baud_rate
        self._reconnect_stop.clear()
        self.device_metadata = None

        if port and not auto_detect:
            self.reconnect_port = port
            self.reconnect_baud = baud
            discovery_port, metadata, discovery_error = discover_device(preferred_port=port, baud=baud, allow_search=False)
            if discovery_port is None:
                self.connected = False
                self.esp32 = None
                if self.auto_reconnect_enabled:
                    self._schedule_reconnect()
                return False, f"ESP32 discovery failed on {port}: {discovery_error}"
            # Use the discovered canonical port when attempting to open the serial
            # connection (discovery may normalize device names / casing).
            result, message = self._attempt_connect(discovery_port, baud, wait_for_device=wait_for_device)
            if result:
                # update reconnect_port to the actual opened port and attach metadata
                self.reconnect_port = discovery_port
                self.device_metadata = metadata
                return True, message
            self.connected = False
            self.esp32 = None
            if self.auto_reconnect_enabled:
                self._schedule_reconnect()
            return False, message

        if auto_detect:
            preferred_port = port if port else None
            candidate_port, metadata, error = discover_device(preferred_port=preferred_port, baud=baud)
            if candidate_port:
                self.reconnect_port = candidate_port
                self.reconnect_baud = baud
                result, message = self._attempt_connect(candidate_port, baud, wait_for_device=wait_for_device)
                if result:
                    self.device_metadata = metadata
                    return True, message
                log.warning(
                    "ESP32 discovery succeeded but could not open port",
                    port=candidate_port,
                    baud=baud,
                    error=message,
                )
                last_error = message
            else:
                last_error = error

            self.connected = False
            self.esp32 = None
            if self.auto_reconnect_enabled:
                self._schedule_reconnect()
            return False, last_error

        if not port:
            port = get_default_com_port(CONFIG.com_port)

        if port:
            self.reconnect_port = port
            self.reconnect_baud = baud
            result, message = self._attempt_connect(port, baud, wait_for_device=wait_for_device)
            if result:
                return True, message
            self.connected = False
            self.esp32 = None
            if self.auto_reconnect_enabled:
                self._schedule_reconnect()
            return False, message

        self.connected = False
        self.esp32 = None
        return False, "No COM port specified"

    def disconnect(self) -> None:
        """Close serial connection cleanly and stop reconnect attempts."""
        with self._lock:
            self._reconnect_stop.set()
            self._join_reconnect_thread()

            if self.esp32 is not None and getattr(self.esp32, "is_open", False):
                try:
                    self.esp32.write(("{\"type\":\"status\",\"state\":\"HOST_DISCONNECTED\"}\n").encode("utf-8"))
                except Exception:
                    pass
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
            self.device_metadata = None

        log.info("Disconnected from ESP32", port=self.reconnect_port, baud=self.reconnect_baud)

    def test_connection(self, port: str, baud: int) -> Tuple[bool, str]:
        """Try a serial connection once without triggering reconnect logic."""
        with self._lock:
            return self._attempt_connect(port, baud)

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
                raw = self.esp32.read(self.esp32.in_waiting or 1)
            except Exception as exc:
                log.error("Serial read error", error=str(exc))
                self.connected = False
                self._schedule_reconnect()
                return None

        if not raw:
            return None

        # Protect read buffer manipulation with the same lock to avoid races
        # if read_line is called from multiple threads.
        with self._lock:
            self._read_buffer += raw
            if b"\n" not in self._read_buffer:
                return None

            line_bytes, _, remainder = self._read_buffer.partition(b"\n")
            self._read_buffer = remainder

        try:
            line = line_bytes.decode("utf-8", errors="ignore")
        except Exception:
            return None

        line = line.rstrip("\r")
        if not line.strip():
            return None
        return line

    def should_ignore(self, line: str) -> bool:
        """Returns True for boot noise, single-character status lines, and ESP32 help text."""
        stripped = line.strip()
        if stripped == ".":
            return True
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

    def _attempt_connect(
        self,
        port: Optional[str],
        baud: Optional[int],
        wait_for_device: bool = False,
    ) -> Tuple[bool, str]:
        if serial is None or port is None or baud is None:
            return False, "serial unavailable"

        try:
            if self.esp32 is not None and getattr(self.esp32, "is_open", False):
                self.esp32.close()
            self.esp32 = serial.Serial(port, baud, timeout=0)
            if wait_for_device:
                time.sleep(2)
            self.connected = True
            self.reconnect_port = port
            self.reconnect_baud = baud
            self.reconnect_count = 0
            log.success("Connected to ESP32", port=port, baud=baud)
            try:
                if self.esp32 is not None and getattr(self.esp32, "is_open", False):
                    self.esp32.write(("{\"type\":\"status\",\"state\":\"HOST_CONNECTED\"}\n").encode("utf-8"))
            except Exception:
                pass
            return True, "OK"
        except Exception as exc:
            self.connected = False
            self.esp32 = None
            return False, str(exc)
