"""Opt-in physical ESP32 smoke test for the maintained V3 serial contract."""

import os
import time

import pytest

if os.getenv("DSIS_RUN_HARDWARE") != "1":
    pytest.skip("Set DSIS_RUN_HARDWARE=1 to run against a physical ESP32", allow_module_level=True)

from core.commands import cmd_enroll, cmd_list, cmd_scan, cmd_stop
from core.serial_handler import SerialHandler, list_serial_ports


def _connect_hardware():
    handler = SerialHandler()
    connected, message = handler.connect(port="", baud=115200, auto_detect=True)
    assert connected, message
    return handler


def _collect_lines(handler, seconds=1.5):
    lines = []
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        line = handler.read_line()
        if line:
            lines.append(line)
    return lines


def test_physical_esp32_v3_safe_lifecycle():
    ports = list_serial_ports()
    assert ports, "No serial ports are visible to Windows"

    handler = _connect_hardware()
    try:
        assert cmd_list(handler) is True
        list_lines = _collect_lines(handler)
        print(f"Physical LIST response: {list_lines}")
        assert any("Stored fingerprints" in line for line in list_lines), list_lines

        assert cmd_scan(handler) is True
        scan_lines = _collect_lines(handler, seconds=0.5)
        assert handler.is_connected()
        assert cmd_stop(handler) is True
        _collect_lines(handler, seconds=0.5)

        assert cmd_enroll(handler) is True
        enroll_lines = _collect_lines(handler, seconds=0.75)
        assert cmd_stop(handler) is True
        _collect_lines(handler, seconds=0.75)
        assert handler.is_connected()
        assert list_lines or scan_lines or enroll_lines
    finally:
        handler.disconnect()

    assert handler.is_connected() is False


@pytest.mark.skipif(
    os.getenv("DSIS_RUN_DESTRUCTIVE_HARDWARE") != "1",
    reason="Set DSIS_RUN_DESTRUCTIVE_HARDWARE=1 only for an approved test device",
)
def test_physical_esp32_empty_device_wipe_and_absent_delete():
    handler = _connect_hardware()
    try:
        assert cmd_list(handler) is True
        list_lines = _collect_lines(handler)
        assert any("Stored fingerprints: 0" in line for line in list_lines), list_lines

        assert handler.send_command("WIPE") is True
        wipe_lines = _collect_lines(handler, seconds=2.0)
        assert any("All fingerprints deleted" in line for line in wipe_lines), wipe_lines

        assert handler.send_command("DELETE:1") is True
        delete_lines = _collect_lines(handler, seconds=1.5)
        assert any("Could not delete ID #1" in line or "not found" in line.lower() for line in delete_lines), delete_lines
    finally:
        handler.disconnect()
