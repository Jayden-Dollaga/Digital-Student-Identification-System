"""ESP32 fingerprint device discovery and handshake support.

This module replaces manual COM port guessing with a structured discovery
workflow. It enumerates serial ports, ranks likely ESP32 candidates, and
validates the device using a JSON handshake handled by the firmware.
"""

import json
import time
from typing import Any, Dict, List, Optional, Tuple, Set, cast

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
    # Use zero-padded 4-digit hex for consistent VID:PID formatting (matches other modules)
    vid_pid = f"{vid:04x}:{pid:04x}" if vid is not None and pid is not None else ""
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
    seen: Set[str] = set()

    def add_port(port: Optional[str]) -> None:
        if not port:
            return
        normalized = port.strip()
        if not normalized:
            return
        key = normalized.upper()
        if key in seen:
            return
        seen.add(key)
        ordered.append(normalized)

    actual_ports: List[str] = []
    port_candidates: List[str] = []
    if list_ports is not None:
        try:
            ports = list_ports.comports()
            actual_ports = [port.device for port in ports if getattr(port, "device", None)]
            scored = [(_score_port_info(port), port.device) for port in ports if getattr(port, "device", None)]
            scored.sort(key=lambda item: item[0], reverse=True)
            port_candidates = [device for _score, device in scored]
        except Exception as exc:
            log.warning("Unable to score serial ports", error=str(exc))
            actual_ports = list_serial_ports()
    else:
        actual_ports = list_serial_ports()

    if actual_ports:
        normalized_actual = {port.upper(): port for port in actual_ports}
        if preferred_port:
            pref_key = preferred_port.strip().upper()
            if pref_key in normalized_actual:
                add_port(normalized_actual[pref_key])
            else:
                log.info(
                    "Preferred port not present in current enumeration; skipping stale preferred port",
                    preferred_port=preferred_port,
                    available_ports=actual_ports,
                )
        default_port = get_default_com_port(CONFIG.com_port)
        if default_port:
            default_key = default_port.strip().upper()
            if default_key in normalized_actual:
                add_port(normalized_actual[default_key])
            else:
                log.info(
                    "Default COM port not present in current enumeration; skipping stale default port",
                    default_port=default_port,
                    available_ports=actual_ports,
                )
        for device in port_candidates or actual_ports:
            add_port(device)
    else:
        if preferred_port:
            add_port(preferred_port)
        default_port = get_default_com_port(CONFIG.com_port)
        add_port(default_port)
        if not ordered:
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

    if isinstance(parsed, dict):
        return cast(Dict[str, Any], parsed)
    return None


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


def _probe_port(port: str, baud: int, timeout: float) -> Tuple[bool, Optional[Any], Optional[Dict[str, Any]], str]:
    if serial is None:
        return False, None, None, "pyserial is not installed"

    log.info("Probing port for handshake", port=port, baud=baud, timeout=timeout)
    cable = None
    keep_open = False

    try:
        cable = serial.Serial(port, baud, timeout=timeout, dsrdtr=False, rtscts=False, xonxoff=False)
        try:
            cable.dtr = False
            cable.rts = False
        except Exception:
            pass
        try:
            cable.reset_input_buffer()
        except Exception:
            pass
        try:
            cable.reset_output_buffer()
        except Exception:
            pass

        time.sleep(0.5)
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
                keep_open = True
                return True, cable, metadata, "OK"
            return False, None, None, f"handshake rejected: {reason}"

        return False, None, None, "no handshake response"
    except Exception as exc:
        error_message = str(exc)
        if cable is not None and getattr(cable, "is_open", False):
            try:
                cable.close()
            except Exception:
                pass
        if "Access is denied" in error_message or "PermissionError" in error_message:
            return False, None, None, (
                "PermissionError(13, 'Access is denied.'): Port in use by another application or USB driver issue. "
                "Check Device Manager or close any serial terminal using the port."
            )
        return False, None, None, error_message
    finally:
        if cable is not None and not keep_open:
            try:
                cable.close()
            except Exception:
                pass


def discover_device(
    preferred_port: Optional[str] = None,
    baud: int = 115200,
    allow_search: bool = True,
    timeout: float = HANDSHAKE_TIMEOUT_SECONDS,
) -> Tuple[Optional[str], Optional[Any], Optional[Dict[str, Any]], str]:
    """Discover the ESP32 fingerprint device and return its port, open serial object, and metadata."""
    if serial is None:
        return None, None, None, "pyserial is not installed"

    candidates = _ordered_candidate_ports(preferred_port if preferred_port else None)
    if not candidates:
        return None, None, None, "no serial ports available"

    log.info(
        "Starting ESP32 discovery",
        preferred_port=preferred_port,
        baud=baud,
        candidates=candidates,
    )

    if not allow_search and preferred_port:
        success, cable, metadata, error = _probe_port(preferred_port, baud, timeout)
        if success:
            return preferred_port, cable, metadata, ""
        return None, None, None, error

    errors: List[str] = []
    for candidate in candidates:
        success, cable, metadata, error = _probe_port(candidate, baud, timeout)
        if success:
            log.success("ESP32 discovery succeeded", port=candidate, metadata=metadata)
            return candidate, cable, metadata, ""

        if error:
            errors.append(f"{candidate}: {error}")
            log.warning("ESP32 discovery probe failed", port=candidate, baud=baud, error=error)
        else:
            log.warning("ESP32 discovery probe timed out", port=candidate, baud=baud)

        if not allow_search and preferred_port:
            # Keep the user informed when probing only the explicitly requested port.
            log.warning("ESP32 discovery failed", port=candidate, baud=baud, error=error)
            break

    if allow_search and errors:
        # Identify critical errors (access denied) that block actual devices
        access_errors = [e for e in errors if "PermissionError(13, 'Access is denied" in e or "Access is denied" in e]
        
        if access_errors:
            # At least one port is blocked—this is often the real device
            summary = (
                access_errors[0]
                if len(access_errors) == 1
                else f"Access denied on {len(access_errors)} ports (likely real devices); first: {access_errors[0]}"
            )
            log.warning("ESP32 discovery failed - port access blocked", baud=baud, error=summary, all_errors=errors)
        else:
            # No access errors; all ports either don't exist or have no device
            summary = (
                errors[0]
                if len(errors) == 1
                else f"{len(errors)} ports probed; common issues: device not found or incorrect port. Errors: {', '.join(errors)}"
            )
            log.warning("ESP32 discovery failed", baud=baud, error=summary)
        return None, None, None, summary

    if errors:
        return None, None, None, errors[0]

    return None, None, None, "no matching ESP32 device found"
