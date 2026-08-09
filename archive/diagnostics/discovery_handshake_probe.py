"""Standalone diagnostic probe for ESP32 discovery handshake.

This script mirrors the application discovery handshake exactly and prints raw
TX/RX bytes for each probed serial port.
"""

from __future__ import annotations

import argparse
import json
import time
from typing import Any, Dict, List, Optional

try:
    import serial
    from serial.tools import list_ports
except ImportError as exc:
    raise SystemExit("pyserial is required. Install with: pip install pyserial") from exc

HANDSHAKE_COMMAND = "ID?"
DEFAULT_BAUD = 115200
DEFAULT_TIMEOUT = 2.0
DEFAULT_STARTUP_DELAY = 0.1
EXPECTED_DEVICE_IDENTIFIER = "Fingerprint Attendance"


def list_available_ports() -> List[str]:
    try:
        return [port.device for port in list_ports.comports() if getattr(port, "device", None)]
    except Exception as exc:
        print(f"Failed to enumerate serial ports: {exc}")
        return []


def parse_expected_handshake(raw_line: bytes) -> Optional[Dict[str, Any]]:
    try:
        text = raw_line.decode("utf-8", errors="ignore").strip()
    except Exception:
        return None
    if not text.startswith("{"):
        return None
    try:
        parsed = json.loads(text)
    except Exception:
        return None
    if parsed.get("device") == EXPECTED_DEVICE_IDENTIFIER:
        return parsed
    return None


def probe_port(port: str, baud: int, timeout: float, startup_delay: float) -> None:
    print(f"\n=== PORT: {port} ===")
    try:
        ser = serial.Serial(
            port,
            baud,
            timeout=timeout,
            dsrdtr=False,
            rtscts=False,
            xonxoff=False,
        )
    except Exception as exc:
        print(f"OPEN FAILED: {exc}")
        return

    try:
        try:
            ser.dtr = False
            ser.rts = False
        except Exception:
            pass

        try:
            ser.reset_input_buffer()
        except Exception as exc:
            print(f"warning: failed to reset input buffer: {exc}")
        try:
            ser.reset_output_buffer()
        except Exception as exc:
            print(f"warning: failed to reset output buffer: {exc}")

        print("OPEN OK")
        print(
            f"settings: baud={ser.baudrate}, timeout={ser.timeout}, dsrdtr={ser.dsrdtr}, "
            f"rtscts={ser.rtscts}, xonxoff={ser.xonxoff}, dtr={ser.dtr}, rts={ser.rts}"
        )

        print(f"Waiting {startup_delay:.3f}s before sending handshake...")
        pre_start = time.time()
        while time.time() - pre_start < startup_delay:
            try:
                raw = ser.readline()
            except Exception as exc:
                print(f"READ FAILED DURING PRE-SEND WAIT: {exc}")
                break
            if not raw:
                continue
            timestamp = time.time()
            try:
                text = raw.decode("utf-8", errors="replace").rstrip("\r\n")
            except Exception:
                text = repr(raw)
            print(f"[{timestamp:.3f}] PRE-SEND RX BYTES: {repr(raw)}")
            print(f"[{timestamp:.3f}] PRE-SEND RX TEXT: {text!r}")

        tx_bytes = (HANDSHAKE_COMMAND + "\n").encode("utf-8")
        print(f"TX BYTES: {repr(tx_bytes)}")
        print(f"TX TEXT: {HANDSHAKE_COMMAND!r}")
        try:
            ser.write(tx_bytes)
            ser.flush()
        except Exception as exc:
            print(f"WRITE FAILED: {exc}")
            return

        deadline = time.time() + timeout
        received_bytes = b""
        responses: List[bytes] = []
        expected_metadata: Optional[Dict[str, Any]] = None

        while time.time() < deadline:
            try:
                raw = ser.readline()
            except Exception as exc:
                print(f"READ FAILED: {exc}")
                break
            if not raw:
                continue
            timestamp = time.time()
            received_bytes += raw
            responses.append(raw)
            try:
                text = raw.decode("utf-8", errors="replace")
            except Exception:
                text = repr(raw)
            print(f"[{timestamp:.3f}] RX BYTES: {repr(raw)}")
            print(f"[{timestamp:.3f}] RX TEXT: {text.strip()!r}")
            if parse_expected_handshake(raw) is not None:
                expected_metadata = parse_expected_handshake(raw)
                break

        print("RESULT:")
        if expected_metadata is not None:
            print("HANDSHAKE: PASS")
            print(f"METADATA: {json.dumps(expected_metadata, indent=2)}")
        elif responses:
            print("HANDSHAKE: FAIL")
            print("Received lines but none matched expected device identifier.")
        else:
            print("HANDSHAKE: TIMEOUT")
            print("No response received within timeout.")

        print(f"TOTAL RX BYTES: {repr(received_bytes)}")
        print(f"TOTAL RX TEXT: {received_bytes.decode('utf-8', errors='replace')!r}")
    finally:
        try:
            ser.close()
            print("CLOSED")
        except Exception as exc:
            print(f"FAILED TO CLOSE: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe ESP32 discovery handshake on serial ports.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--probe-all", action="store_true", help="Probe all available COM ports")
    group.add_argument("--port", help="Probe a single COM port")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD, help="Baud rate to use")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="Handshake read timeout in seconds")
    parser.add_argument("--startup-delay", type=float, default=DEFAULT_STARTUP_DELAY, help="Delay after opening port before sending handshake")
    args = parser.parse_args()

    if args.probe_all:
        ports = list_available_ports()
        if not ports:
            print("No serial ports detected.")
            return
        print(f"Detected ports: {ports}")
        for port in ports:
            probe_port(port, args.baud, args.timeout, args.startup_delay)
    else:
        probe_port(args.port, args.baud, args.timeout, args.startup_delay)


if __name__ == "__main__":
    main()
