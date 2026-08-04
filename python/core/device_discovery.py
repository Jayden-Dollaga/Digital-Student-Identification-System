"""ESP32 fingerprint device discovery and handshake support.

This module replaces manual COM port guessing with a structured discovery
workflow. It enumerates serial ports, ranks likely ESP32 candidates, and
validates the device using a JSON handshake handled by the firmware.
"""

import json
import time
from typing import Any, Dict, List, Optional, Tuple

try:
    import serial
    from serial.tools import list_ports
except ModuleNotFoundError:  # pragma: no cover
    serial = None
    list_ports = None

from config import get_config, get_default_com_port
from core.logger import log

CONFIG = get_config()

SUPPORTED_DEVICE_IDENTIFIER = "Fingerprint Attendance"
MIN_PROTOCOL_VERSION = 1
HANDSHAKE_COMMAND = "ID?"
HANDSHAKE_TIMEOUT_SECONDS = 2.0
STATIC_PORT_CANDIDATES = [
    "COM1", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "COM10", "COM11", "COM12",
]
KNOWN_DEVICE_KEYWORDS = [
    "esp32", "cp210", "ch340", "usb serial", "silicon labs", "uart", "arduino",
]
KNOWN_NON_DEVICE_KEYWORDS = ["bluetooth", "bt"]
KNOWN_VID_PID_SCORES = {
    "10c4:ea60": 140,
    "1a86:7523": 140,
    "0403:6001": 120,
    "1a86:55d3": 120,
}


def list_serial_ports() -> List[str]:
    """Return a list of available serial ports."""
    if list_ports is None:
        return []

    try:
        return [port.device for port in list_ports.comports() if getattr(port, "device", None)]
    except Exception as exc:
        log.warning("Failed to enumerate serial ports", error=str(exc))
        return []


def _score_port_info(port_info: Any) -> int:
    score = 0
    description = (getattr(port_info, "description", "") or "").lower()
    device = (getattr(port_info, "device", "") or "").lower()
    combined = f"{device} {description}".strip()

    vid = getattr(port_info, "vid", None)
    pid = getattr(port_info, "pid", None)
    vid_pid = f"{vid:x}:{pid:x}" if vid is not None and pid is not None else ""
    if vid_pid in KNOWN_VID_PID_SCORES:
        score += KNOWN_VID_PID_SCORES[vid_pid]

    for keyword in KNOWN_DEVICE_KEYWORDS:
        if keyword in combined:
            score += 80

    for keyword in KNOWN_NON_DEVICE_KEYWORDS:
        if keyword in combined:
            score -= 100

    if "com" in device:
        score += 10
    if "usb" in combined:
        score += 10

    return score


def _ordered_candidate_ports(preferred_port: Optional[str] = None) -> List[str]:
    """Build an ordered list of ports to probe for the ESP32 device."""
    ordered: List[str] = []
    seen = set()

    def add_port(port: Optional[str]) -> None:
        if not port:
            return
        normalized = port.strip()
        if not normalized or normalized in seen:
            return
        seen.add(normalized)
        ordered.append(normalized)

    add_port(preferred_port)
    add_port(get_default_com_port(CONFIG.com_port))

    if list_ports is not None:
        try:
            ports = list_ports.comports()
            scored = [(_score_port_info(port), port.device) for port in ports if getattr(port, "device", None)]
            scored.sort(key=lambda item: item[0], reverse=True)
            for _score, device in scored:
                add_port(device)
        except Exception as exc:
            log.warning("Unable to score serial ports", error=str(exc))

    for port in list_serial_ports():
        add_port(port)

    for port in STATIC_PORT_CANDIDATES:
        add_port(port)

    return ordered


def _parse_json_line(line: str) -> Optional[Dict[str, Any]]:
    if not line or not line.strip().startswith("{"):
        return None

    try:
        parsed = json.loads(line.strip())
    except Exception:
        return None

    return parsed if isinstance(parsed, dict) else None


def _validate_handshake(metadata: Dict[str, Any]) -> Tuple[bool, str]:
    if not metadata:
        return False, "empty handshake payload"

    if metadata.get("device") != SUPPORTED_DEVICE_IDENTIFIER:
        return False, f"unexpected device identifier: {metadata.get('device')!r}"

    protocol = metadata.get("protocol")
    if isinstance(protocol, str):
        protocol = protocol.strip()
        if protocol.isdigit():
            protocol = int(protocol)
    if not isinstance(protocol, int):
        return False, "protocol version missing or invalid"

    if protocol < MIN_PROTOCOL_VERSION:
        return False, f"protocol version {protocol} is lower than supported {MIN_PROTOCOL_VERSION}"

    return True, "OK"


def _probe_port(port: str, baud: int, timeout: float) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    if serial is None:
        return False, None, "pyserial is not installed"

    try:
        with serial.Serial(port, baud, timeout=timeout) as cable:
            cable.reset_input_buffer()
            cable.reset_output_buffer()
            time.sleep(0.1)
            cable.write((HANDSHAKE_COMMAND + "\n").encode("utf-8"))
            cable.flush()

            deadline = time.time() + timeout
            while time.time() < deadline:
                raw = cable.readline()
                if not raw:
                    continue
                try:
                    line = raw.decode("utf-8", errors="ignore").strip()
                except Exception:
                    continue
                if not line:
                    continue
                metadata = _parse_json_line(line)
                if metadata is None:
                    continue
                valid, reason = _validate_handshake(metadata)
                if valid:
                    return True, metadata, "OK"
                return False, None, f"handshake rejected: {reason}"
    except Exception as exc:
        return False, None, str(exc)

    return False, None, "no handshake response"


def discover_device(
    preferred_port: Optional[str] = None,
    baud: int = 115200,
    allow_search: bool = True,
    timeout: float = HANDSHAKE_TIMEOUT_SECONDS,
) -> Tuple[Optional[str], Optional[Dict[str, Any]], str]:
    """Discover the ESP32 fingerprint device and return its port and metadata."""
    if serial is None:
        return None, None, "pyserial is not installed"

    candidates = _ordered_candidate_ports(preferred_port if preferred_port else None)
    if not candidates:
        return None, None, "no serial ports available"

    log.info("Starting ESP32 discovery", preferred_port=preferred_port, baud=baud, candidates=candidates)

    if not allow_search and preferred_port:
        success, metadata, error = _probe_port(preferred_port, baud, timeout)
        if success:
            return preferred_port, metadata, ""
        return None, None, error

    last_error = ""
    for candidate in candidates:
        if preferred_port and candidate.lower() == preferred_port.lower():
            success, metadata, error = _probe_port(candidate, baud, timeout)
        else:
            success, metadata, error = _probe_port(candidate, baud, timeout)

        if success:
            log.success("ESP32 discovery succeeded", port=candidate, metadata=metadata)
            return candidate, metadata, ""

        last_error = f"{candidate}: {error}" if error else last_error
        log.warning("ESP32 discovery failed", port=candidate, baud=baud, error=error)
        if not allow_search and preferred_port:
            break

    return None, None, last_error or "no matching ESP32 device found"
