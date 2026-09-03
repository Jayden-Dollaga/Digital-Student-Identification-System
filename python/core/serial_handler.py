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
from settings_store import cleanup_stale_port

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
        self._pending_raw_lines: List[str] = []
        self.auto_reconnect_enabled = CONFIG.auto_reconnect
        self._auto_detect_requested = False
        self._preferred_port: Optional[str] = None
        self._pyserial_missing_warning_shown = False
        self._has_ever_connected = False  # Track if we've had a successful connection
        self._lock = threading.RLock()
        self._reconnect_thread: Optional[threading.Thread] = None
        self._reconnect_stop = threading.Event()
        self._read_buffer = b""
        self._last_read_idle_log = 0.0
        log.info(
            "SerialHandler initialized",
            thread_id=threading.get_ident(),
            thread_name=threading.current_thread().name,
        )

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

        log.info(
            "SerialHandler.connect() entered",
            port=port,
            baud=baud,
            wait_for_device=wait_for_device,
            auto_detect=auto_detect,
            thread_id=threading.get_ident(),
            thread_name=threading.current_thread().name,
        )

        with self._lock:
            self._reconnect_stop.clear()
            self.device_metadata = None
            self._preferred_port = None
            self._auto_detect_requested = False

            if port and not auto_detect:
                self.reconnect_port = port
                self.reconnect_baud = baud
                self._auto_detect_requested = False

                # Before even trying to open the port, check whether it's
                # still a real port on this machine. A com_port value saved
                # in settings.json on one PC (or carried over in a portable
                # data/ folder) is frequently stale on another - e.g. saved
                # as "COM4" but this machine enumerates the ESP32 on "COM5".
                # Previously this went straight to a search=False probe of
                # the stale port, which fails outright with no recovery
                # short of the user clearing settings.json by hand. Now we
                # detect staleness up front and fall back to a real search
                # so a saved-but-wrong port behaves like "no port saved" on
                # a new machine, instead of hard-locking the app to it.
                available_ports = list_serial_ports()
                cleaned_port = cleanup_stale_port(port, available_ports)
                if cleaned_port is None:
                    log.warning(
                        "Saved COM port not present on this machine; falling back to auto-detect search",
                        stale_port=port,
                        available_ports=available_ports,
                    )
                    candidate_port, cable, metadata, error = discover_device(
                        preferred_port=None,
                        baud=baud,
                    )
                    if candidate_port is None:
                        self.connected = False
                        self.esp32 = None
                        if self.auto_reconnect_enabled and self._has_ever_connected:
                            self._schedule_reconnect()
                        log.warning(
                            "SerialHandler.connect() exiting after stale-port fallback search failed",
                            stale_port=port,
                            error=error,
                        )
                        return False, (
                            f"Saved port {port} is no longer available on this device, "
                            f"and no ESP32 was found on any other port: {error}"
                        )

                    log.info(
                        "Recovered from stale saved port via auto-detect",
                        stale_port=port,
                        found_port=candidate_port,
                    )
                    if self.esp32 is not None and getattr(self.esp32, "is_open", False):
                        try:
                            self.esp32.close()
                        except Exception:
                            pass
                    self.esp32 = cable
                    if hasattr(cable, '_probe_buffered_lines'):
                        self._pending_raw_lines.extend(cable._probe_buffered_lines)
                    self.esp32.timeout = 0
                    try:
                        self.esp32.reset_input_buffer()
                    except Exception:
                        pass
                    try:
                        self.esp32.reset_output_buffer()
                    except Exception:
                        pass
                    self.connected = True
                    self._has_ever_connected = True
                    self.reconnect_port = candidate_port
                    self.reconnect_baud = baud
                    self.reconnect_count = 0
                    self.device_metadata = metadata
                    log.success(
                        "Connected to ESP32 via stale-port fallback search",
                        port=candidate_port,
                        baud=baud,
                    )
                    return True, f"OK (saved port {port} was stale; reconnected on {candidate_port})"

                discovery_port, cable, metadata, discovery_error = discover_device(
                    preferred_port=port,
                    baud=baud,
                    allow_search=False,
                )
                if discovery_port is None:
                    self.connected = False
                    self.esp32 = None
                    if self.auto_reconnect_enabled and self._has_ever_connected:
                        self._schedule_reconnect()
                    log.warning(
                        "SerialHandler.connect() exiting after explicit port discovery failure",
                        port=port,
                        error=discovery_error,
                    )
                    return False, f"ESP32 discovery failed on {port}: {discovery_error}"

                log.info("Adopting discovered serial connection", port=discovery_port)
                if self.esp32 is not None and getattr(self.esp32, "is_open", False):
                    try:
                        self.esp32.close()
                    except Exception:
                        pass
                self.esp32 = cable
                
                # Extract buffered boot lines from the probe before resetting buffer
                if hasattr(cable, '_probe_buffered_lines'):
                    self._pending_raw_lines.extend(cable._probe_buffered_lines)
                    log.info(
                        "Restored buffered lines from probe",
                        count=len(cable._probe_buffered_lines),
                    )
                
                self.esp32.timeout = 0
                try:
                    self.esp32.reset_input_buffer()
                except Exception:
                    pass
                try:
                    self.esp32.reset_output_buffer()
                except Exception:
                    pass
                self.connected = True
                self._has_ever_connected = True
                self.reconnect_port = discovery_port
                self.reconnect_baud = baud
                self.reconnect_count = 0
                self.device_metadata = metadata
                log.success("Connected to ESP32 via discovered serial", port=discovery_port, baud=baud)
                return True, "OK"

            if auto_detect:
                preferred_port = port if port else None
                self._preferred_port = preferred_port
                self._auto_detect_requested = True
                self.reconnect_port = preferred_port
                self.reconnect_baud = baud
                candidate_port, cable, metadata, error = discover_device(
                    preferred_port=preferred_port,
                    baud=baud,
                )
                if candidate_port:
                    self.reconnect_port = candidate_port
                    self.reconnect_baud = baud
                    log.info("Adopting discovered serial connection", port=candidate_port)
                    if self.esp32 is not None and getattr(self.esp32, "is_open", False):
                        try:
                            self.esp32.close()
                        except Exception:
                            pass
                    self.esp32 = cable
                    
                    # Extract buffered boot lines from the probe before resetting buffer
                    if hasattr(cable, '_probe_buffered_lines'):
                        self._pending_raw_lines.extend(cable._probe_buffered_lines)
                        log.info(
                            "Restored buffered lines from probe",
                            count=len(cable._probe_buffered_lines),
                        )
                    
                    self.esp32.timeout = 0
                    try:
                        self.esp32.reset_input_buffer()
                    except Exception:
                        pass
                    try:
                        self.esp32.reset_output_buffer()
                    except Exception:
                        pass
                    self.connected = True
                    self._has_ever_connected = True
                    self.reconnect_count = 0
                    self.device_metadata = metadata
                    log.success("Connected to ESP32 via discovered serial", port=candidate_port, baud=baud)
                    return True, "OK"
                last_error = error

                self.connected = False
                self.esp32 = None
                if self.auto_reconnect_enabled and self._has_ever_connected:
                    self._schedule_reconnect()
                log.warning(
                    "SerialHandler.connect() exiting after auto-detect failure",
                    error=last_error,
                )
                return False, last_error

            self._preferred_port = None
            if not port:
                port = get_default_com_port(CONFIG.com_port)
                # Check if the stored port is stale and clear it if needed
                if port:
                    available = list_serial_ports()
                    cleaned_port = cleanup_stale_port(port, available)
                    port = cleaned_port if cleaned_port else ""

            if port:
                self.reconnect_port = port
                self.reconnect_baud = baud
                result, message = self._attempt_connect(
                    port,
                    baud,
                    wait_for_device=wait_for_device,
                )
                if result:
                    return True, message

                self.connected = False
                self.esp32 = None
                if self.auto_reconnect_enabled:
                    self._schedule_reconnect()
                log.warning(
                    "SerialHandler.connect() exiting after explicit port failure",
                    port=port,
                    error=message,
                )
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

    def reset_device(self) -> bool:
        """
        Deliberately reboot the ESP32 by pulsing DTR low->high->low.
        This is the ONLY place that intentionally resets the device via DTR;
        connect()/reconnect() are careful to avoid doing this accidentally
        (see the dtr-before-open pattern in _attempt_connect / _probe_port).
        Use this when the user explicitly wants to see the fresh boot banner
        (e.g. a "Reset Device" button), not as part of any automatic flow.
        Returns True if the pulse was sent, False if not connected.
        """
        with self._lock:
            if not self.is_connected():
                return False
            try:
                log.info("Pulsing DTR to reset ESP32", port=self.reconnect_port)
                self.esp32.dtr = True
                time.sleep(0.1)
                self.esp32.dtr = False
                # A DTR pulse can inject a stray partial byte or two into the
                # line right as the device resets. If that leftover sits in
                # _read_buffer with no newline yet, every subsequent real
                # boot-text byte gets appended onto it and read_line() won't
                # treat any of it as a complete line until a '\n' eventually
                # shows up - which should happen fast once real text starts,
                # but there's no reason to carry stale bytes into the fresh
                # boot sequence at all. Start clean.
                self._read_buffer = b""
                log.info(
                    "DTR reset pulse complete, read buffer cleared - watching for fresh boot output",
                    port=self.reconnect_port,
                )
                return True
            except Exception as exc:
                log.error("Failed to reset ESP32 via DTR pulse", error=str(exc))
                return False

    def read_line(self) -> Optional[str]:
        """
        Read a single line from ESP32.
        Returns decoded text or None if no complete line is available.
        """
        with self._lock:
            # First, return any buffered lines from the probe (boot messages)
            if self._pending_raw_lines:
                line = self._pending_raw_lines.pop(0)
                log.debug("Returning pending line from probe", line=line[:60] if len(line) > 60 else line)
                return line

            # Drain any already-buffered line(s) BEFORE touching the wire again.
            # A single serial burst often contains multiple '\n'-terminated
            # lines; only the first was returned last call and the rest were
            # left in _read_buffer. If we gate on in_waiting first, those
            # remaining lines get stuck until unrelated new traffic happens
            # to arrive, which is why the GUI log used to lag/drop lines
            # compared to the Arduino IDE Serial Monitor.
            if b"\n" in self._read_buffer:
                line_bytes, _, remainder = self._read_buffer.partition(b"\n")
                self._read_buffer = remainder
            else:
                if not self.is_connected():
                    if self.auto_reconnect_enabled and self.reconnect_port:
                        self._schedule_reconnect()
                    return None

                if self.esp32.in_waiting == 0:
                    # Diagnostic breadcrumb for the "monitor doesn't update
                    # until I send a command" reports - rate-limited so it
                    # doesn't spam the Application Log, but frequent enough
                    # that if this happens again, the log will show exactly
                    # whether the port is genuinely silent (in_waiting stuck
                    # at 0 the whole time) versus data arriving but getting
                    # lost somewhere else in the pipeline.
                    now = time.time()
                    if now - self._last_read_idle_log > 3.0:
                        self._last_read_idle_log = now
                        log.debug(
                            "Serial read idle: in_waiting is 0",
                            port=self.reconnect_port,
                            pending_buffered_lines=len(self._pending_raw_lines),
                            unterminated_buffer_bytes=len(self._read_buffer),
                        )
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
        if not self.auto_reconnect_enabled or (not self.reconnect_port and not self._auto_detect_requested):
            return False
        self._schedule_reconnect()
        return True

    def _schedule_reconnect(self) -> None:
        with self._lock:
            if not self.auto_reconnect_enabled or (not self.reconnect_port and not self._auto_detect_requested):
                log.info(
                    "Reconnect not scheduled",
                    auto_reconnect_enabled=self.auto_reconnect_enabled,
                    reconnect_port=self.reconnect_port,
                    auto_detect_requested=self._auto_detect_requested,
                )
                return

            if self._reconnect_thread is not None and self._reconnect_thread.is_alive():
                log.info(
                    "Reconnect worker already running",
                    thread_name=self._reconnect_thread.name,
                    reconnect_count=self.reconnect_count,
                )
                return

            self._reconnect_stop.clear()
            self._reconnect_thread = threading.Thread(
                target=self._reconnect_worker,
                daemon=True,
                name="SerialHandlerReconnect",
            )
            log.info("Starting reconnect worker", thread_name=self._reconnect_thread.name)
            self._reconnect_thread.start()

    def _join_reconnect_thread(self) -> None:
        thread = self._reconnect_thread
        if thread is None:
            return
        if thread.is_alive():
            thread.join(timeout=1.0)
        self._reconnect_thread = None

    def _reconnect_worker(self) -> None:
        log.info(
            "Reconnect worker entered",
            thread_id=threading.get_ident(),
            thread_name=threading.current_thread().name,
            reconnect_port=self.reconnect_port,
            reconnect_baud=self.reconnect_baud,
            auto_detect=self._auto_detect_requested,
        )
        try:
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
                    auto_detect=self._auto_detect_requested,
                )

                if self._reconnect_stop.wait(delay):
                    return

                with self._lock:
                    if self._reconnect_stop.is_set():
                        return

                    if self._auto_detect_requested:
                        # Auto-detect mode: refresh port enumeration each retry
                        candidate_port, cable, metadata, error = discover_device(
                            preferred_port=self._preferred_port,
                            baud=self.reconnect_baud or CONFIG.baud_rate,
                        )
                        if candidate_port:
                            self.reconnect_port = candidate_port
                            self.device_metadata = metadata
                            self.esp32 = cable
                            self.esp32.timeout = 0
                            try:
                                self.esp32.reset_input_buffer()
                            except Exception:
                                pass
                            try:
                                self.esp32.reset_output_buffer()
                            except Exception:
                                pass
                            self.connected = True
                            self.reconnect_count = 0
                            success, msg = True, "OK"
                        else:
                            success = False
                            msg = error
                    else:
                        # Explicit port mode: check if port still exists; if not and this is a stale port, suggest auto-detect
                        available_ports = list_serial_ports()
                        if self.reconnect_port and self.reconnect_port not in available_ports:
                            if self.reconnect_count > 2:
                                # After a few attempts, suggest switching to auto-detect
                                log.warning(
                                    "Reconnect port no longer available; suggest auto-detect",
                                    port=self.reconnect_port,
                                    available_ports=available_ports,
                                    attempt=self.reconnect_count,
                                )
                                success = False
                                msg = f"Port {self.reconnect_port} not found. Available ports: {available_ports}. Try using auto-detect."
                            else:
                                success = False
                                msg = f"Port {self.reconnect_port} not currently available"
                        else:
                            success, msg = self._attempt_connect(self.reconnect_port, self.reconnect_baud)

                if success:
                    log.success(
                        "Auto-reconnect successful",
                        port=self.reconnect_port,
                        baud=self.reconnect_baud,
                        auto_detect=self._auto_detect_requested,
                    )
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
        except Exception as exc:
            log.exception(
                "Unexpected exception in reconnect worker",
                error=str(exc),
                thread_id=threading.get_ident(),
                thread_name=threading.current_thread().name,
            )
            self.connected = False
            self.esp32 = None
            self._reconnect_stop.set()
        finally:
            log.info(
                "Reconnect worker exiting",
                thread_id=threading.get_ident(),
                thread_name=threading.current_thread().name,
                reconnect_count=self.reconnect_count,
                connected=self.connected,
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
            # IMPORTANT: pyserial defaults dtr/rts to True and asserts them
            # the moment the port opens. On ESP32 boards that edge triggers
            # a hardware reset via the EN pin auto-reset circuit, so every
            # reconnect was silently rebooting the device (which also drops
            # scan mode, since scanMode resets to false on boot). Build the
            # Serial object closed, set dtr/rts first, then open() explicitly
            # so reconnecting no longer resets the ESP32.
            self.esp32 = serial.Serial()
            self.esp32.port = port
            self.esp32.baudrate = baud
            self.esp32.timeout = 0
            self.esp32.dsrdtr = False
            self.esp32.rtscts = False
            self.esp32.xonxoff = False
            try:
                self.esp32.dtr = False
                self.esp32.rts = False
            except Exception:
                pass
            self.esp32.open()
            try:
                self.esp32.reset_input_buffer()
                self.esp32.reset_output_buffer()
            except Exception:
                pass
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
            log.warning(
                "SerialHandler._attempt_connect() failed",
                port=port,
                baud=baud,
                error=str(exc),
                thread_id=threading.get_ident(),
                thread_name=threading.current_thread().name,
            )
            self.connected = False
            self.esp32 = None
            return False, str(exc)