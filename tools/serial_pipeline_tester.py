"""Standalone serial pipeline diagnostic for ESP32 Fingerprint Attendance."""

from __future__ import annotations

import argparse
import binascii
import os
import sys
import time
from typing import List, Optional

try:
    import serial
except ImportError as exc:
    raise SystemExit(
        "pyserial is required for this diagnostic. Install with: pip install pyserial"
    ) from exc


DEFAULT_PORT = "COM4"
DEFAULT_BAUD = 115200
DEFAULT_DURATION = 8.0
DEFAULT_MAX_LINES = 40
TOKEN = b"SPI_FAST_FLASH_BOOT"
MISSING_TOKEN = b"PI_FAST_FLASH_BOOT"


def format_bytes(data: bytes) -> str:
    return " ".join(f"{b:02X}" for b in data)


def format_text(data: bytes) -> str:
    try:
        return data.decode("utf-8", errors="replace")
    except Exception:
        return repr(data)


def inspect_port_settings(port: str, baud: int, timeout: float, clear_dtr_rts: bool = False) -> serial.Serial:
    ser = serial.Serial(
        port,
        baud,
        timeout=timeout,
        dsrdtr=False,
        rtscts=False,
        xonxoff=False,
    )
    if clear_dtr_rts:
        try:
            ser.dtr = False
            ser.rts = False
            ser.reset_input_buffer()
            ser.reset_output_buffer()
        except Exception:
            pass
    return ser


def capture_raw_lines(ser: serial.Serial, max_lines: int, duration: float) -> List[bytes]:
    start = time.time()
    buffer = b""
    lines: List[bytes] = []

    while time.time() - start < duration and len(lines) < max_lines:
        chunk = ser.read(ser.in_waiting or 1)
        if chunk:
            buffer += chunk
            while b"\n" in buffer and len(lines) < max_lines:
                line, sep, buffer = buffer.partition(b"\n")
                lines.append(line)
        else:
            time.sleep(0.02)

    if buffer and len(lines) < max_lines:
        lines.append(buffer)

    return lines


def print_section(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def line_report(index: int, raw_line: bytes) -> None:
    text = format_text(raw_line)
    token_present = TOKEN in raw_line
    missing_token = MISSING_TOKEN in raw_line
    print(f"[LINE {index}] length={len(raw_line)}")
    print(f"TEXT: {text}")
    print(f"REPR: {repr(raw_line)}")
    print(f"HEX : {format_bytes(raw_line)}")
    if token_present:
        print("TOKEN: SPI_FAST_FLASH_BOOT FOUND")
    elif missing_token:
        print("TOKEN: PI_FAST_FLASH_BOOT FOUND (missing leading S)")
    elif b"FAST_FLASH_BOOT" in raw_line:
        print("TOKEN: FAST_FLASH_BOOT found but not full SPI_FAST_FLASH_BOOT")
    print("-")


def find_token_evidence(raw_lines: List[bytes]) -> None:
    found = False
    for idx, raw_line in enumerate(raw_lines):
        if TOKEN in raw_line or MISSING_TOKEN in raw_line or b"FAST_FLASH_BOOT" in raw_line:
            print(f"[TOKEN EVIDENCE] line={idx}")
            line_report(idx, raw_line)
            found = True
    if not found:
        print("[TOKEN EVIDENCE] no boot token line found in captured data")


def run_raw_capture(port: str, baud: int, duration: float, max_lines: int) -> None:
    print_section("ESP32 SERIAL PIPELINE DIAGNOSTIC")
    print(f"PORT: {port}")
    print(f"BAUD: {baud}")
    print(f"DURATION: {duration}s")
    print(f"MAX LINES: {max_lines}")

    for clear_dtr_rts in (False, True):
        label = "default open" if not clear_dtr_rts else "clear DTR/RTS after open"
        print_section(f"RAW BYTE CAPTURE ({label})")
        print("Opening the port may reset the ESP32. Waiting for boot output...")

        try:
            ser = inspect_port_settings(port, baud, timeout=0.2, clear_dtr_rts=clear_dtr_rts)
        except Exception as exc:
            print(f"Failed to open {port} with {label}: {exc}")
            continue

        try:
            print_section("PORT SETTINGS")
            print(f"port     : {ser.port}")
            print(f"baudrate : {ser.baudrate}")
            print(f"bytesize : {ser.bytesize}")
            print(f"parity   : {ser.parity}")
            print(f"stopbits : {ser.stopbits}")
            print(f"timeout  : {ser.timeout}")
            print(f"xonxoff  : {ser.xonxoff}")
            print(f"rtscts   : {ser.rtscts}")
            print(f"dsrdtr   : {ser.dsrdtr}")
            print(f"dtr      : {ser.dtr}")
            print(f"rts      : {ser.rts}")

            raw_lines = capture_raw_lines(ser, max_lines=max_lines, duration=duration)
            if not raw_lines:
                print("No lines captured. The port is open but no data was received.")
                continue

            for idx, raw_line in enumerate(raw_lines):
                line_report(idx, raw_line)

            print_section("CHARACTER INTEGRITY TEST")
            find_token_evidence(raw_lines)

            print_section("RESULT")
            raw_ok = any(TOKEN in raw_line for raw_line in raw_lines)
            missing_ok = any(MISSING_TOKEN in raw_line for raw_line in raw_lines)
            if raw_ok:
                print("RAW SERIAL: PASS — full SPI_FAST_FLASH_BOOT seen in raw capture.")
            elif missing_ok:
                print("RAW SERIAL: FAIL — captured PI_FAST_FLASH_BOOT without leading S.")
            else:
                print("RAW SERIAL: WARNING — no boot token line with FAST_FLASH_BOOT was captured.")
        finally:
            try:
                ser.close()
            except Exception:
                pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Standalone serial pipeline diagnostic for ESP32 Fingerprint Attendance."
    )
    parser.add_argument("--port", default=DEFAULT_PORT, help="Serial port to use (default COM4)")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD, help="Baud rate (default 115200)")
    parser.add_argument("--duration", type=float, default=DEFAULT_DURATION, help="Capture duration in seconds")
    parser.add_argument("--max-lines", type=int, default=DEFAULT_MAX_LINES, help="Maximum number of lines to capture")
    parser.add_argument("--mode", choices=["raw"], default="raw", help="Diagnostic mode")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.mode == "raw":
        run_raw_capture(args.port, args.baud, args.duration, args.max_lines)
    else:
        raise SystemExit(f"Unknown mode: {args.mode}")


if __name__ == "__main__":
    main()
