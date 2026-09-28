"""Mocked-serial regression tests for ESP32 discovery and connect fallback behavior.

These tests avoid real serial hardware entirely. They exercise the discovery and
connection code paths using fake port listings and fake Serial objects so the
failure modes are stable and fast under pytest.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from core import device_discovery
import core.serial_handler as serial_handler_module
from core.serial_handler import SerialHandler

VALID_DEVICE_JSON = (
    '{"device": "Digital Student Identification System", "board": "ESP32", '
    '"firmware": "1.2.5", "sensor": "AS608", "protocol": 1}'
)
WRONG_DEVICE_JSON = '{"device": "Not DSIS", "protocol": 1}'


class FakePortInfo:
    def __init__(self, device: str, description: str = "USB Serial", vid: int | None = None, pid: int | None = None):
        self.device = device
        self.description = description
        self.vid = vid
        self.pid = pid


class FakeSerial:
    def __init__(self, boot_lines=None, reply_lines=None, open_error=None):
        self._boot_lines = list(boot_lines or [])
        self._reply_lines = list(reply_lines or [])
        self._open_error = open_error
        self.port = None
        self.baudrate = None
        self.timeout = None
        self.dsrdtr = None
        self.rtscts = None
        self.xonxoff = None
        self.dtr = None
        self.rts = None
        self.is_open = False
        self.write_calls = []

    def open(self):
        if self._open_error is not None:
            raise self._open_error
        self.is_open = True

    @property
    def in_waiting(self):
        return len(self._boot_lines)

    def write(self, data):
        self.write_calls.append(data)

    def flush(self):
        pass

    def reset_input_buffer(self):
        pass

    def reset_output_buffer(self):
        pass

    def readline(self):
        if self._boot_lines:
            return (self._boot_lines.pop(0) + "\n").encode("utf-8")
        if self._reply_lines:
            return (self._reply_lines.pop(0) + "\n").encode("utf-8")
        return b""

    def close(self):
        self.is_open = False


class FakeConnectedCable(FakeSerial):
    def __init__(self):
        super().__init__()
        self.is_open = True

    def write(self, data):
        self.write_calls.append(data)


class FakeListPorts:
    def __init__(self, ports):
        self._ports = ports

    def comports(self):
        return self._ports


pytestmark = pytest.mark.integration


def test_discover_device_falls_back_to_second_candidate(monkeypatch):
    """If the first candidate is wrong, discovery should continue to the next valid port."""
    calls = []

    def fake_probe(port, baud, timeout):
        calls.append(port)
        if port == "COM6":
            return False, None, None, "handshake rejected: unexpected device identifier: 'Wrong Board'"
        if port == "COM4":
            return True, object(), {"device": "Digital Student Identification System", "protocol": 1}, "OK"
        return False, None, None, "no handshake response"

    monkeypatch.setattr(device_discovery, "_ordered_candidate_ports", lambda preferred=None: ["COM6", "COM4"])
    monkeypatch.setattr(device_discovery, "_probe_port", fake_probe)

    port, cable, metadata, error = device_discovery.discover_device(preferred_port=None, allow_search=True)

    assert port == "COM4"
    assert cable is not None
    assert metadata["device"] == "Digital Student Identification System"
    assert error == ""
    assert calls == ["COM6", "COM4"]


def test_probe_rejects_wrong_device_identity(monkeypatch):
    """Wrong hardware should not be accepted just because it speaks JSON on serial."""
    fake_module = type(sys)("fake_serial")
    fake_module.Serial = lambda: FakeSerial(reply_lines=[WRONG_DEVICE_JSON])
    monkeypatch.setattr(device_discovery, "serial", fake_module)
    monkeypatch.setattr(device_discovery.time, "sleep", lambda seconds: None)

    success, cable, metadata, error = device_discovery._probe_port("COM4", 115200, timeout=0.1)

    assert success is False
    assert metadata is None
    assert "handshake rejected" in error
    assert "unexpected device identifier" in error
    assert cable is None


def test_probe_timeout_returns_no_handshake_response(monkeypatch):
    """Silent ports should fail cleanly instead of hanging or reporting a false positive."""
    fake_module = type(sys)("fake_serial")
    fake_module.Serial = lambda: FakeSerial()
    monkeypatch.setattr(device_discovery, "serial", fake_module)
    monkeypatch.setattr(device_discovery.time, "sleep", lambda seconds: None)

    success, cable, metadata, error = device_discovery._probe_port("COM4", 115200, timeout=0.05)

    assert success is False
    assert cable is None
    assert metadata is None
    assert error == "no handshake response"


def test_probe_validates_boot_output_before_id_query(monkeypatch):
    """A valid handshake already visible in boot output should succeed without waiting for ID?."""
    fake_module = type(sys)("fake_serial")
    fake_module.Serial = lambda: FakeSerial(boot_lines=[VALID_DEVICE_JSON])
    monkeypatch.setattr(device_discovery, "serial", fake_module)
    monkeypatch.setattr(device_discovery.time, "sleep", lambda seconds: None)

    success, cable, metadata, error = device_discovery._probe_port("COM4", 115200, timeout=0.25)

    assert success is True
    assert error == "OK"
    assert metadata["device"] == "Digital Student Identification System"
    assert cable is not None
    assert getattr(cable, "write_calls", []) == []


def test_connect_handles_stale_saved_port_by_auto_detecting_new_port(monkeypatch):
    """A saved-but-stale COM port should fall back to live auto-detection instead of failing permanently."""
    handler = SerialHandler()
    handler.auto_reconnect_enabled = False

    fake_cable = FakeConnectedCable()

    monkeypatch.setattr(serial_handler_module, "cleanup_stale_port", lambda port, available: None)
    monkeypatch.setattr(serial_handler_module, "discover_device", lambda preferred_port=None, baud=115200, allow_search=True, timeout=3.0: ("COM4", fake_cable, {"device": "Digital Student Identification System", "protocol": 1}, ""))

    result, message = handler.connect(port="COM99", baud=115200, auto_detect=False)

    assert result is True
    assert "saved port COM99" in message
    assert handler.reconnect_port == "COM4"
    assert handler.device_metadata["device"] == "Digital Student Identification System"


def test_connect_reports_access_denied_when_port_is_in_use(monkeypatch):
    """A blocked port should surface a clear access-denied error instead of a generic timeout."""
    handler = SerialHandler()
    handler.auto_reconnect_enabled = False

    monkeypatch.setattr(serial_handler_module, "cleanup_stale_port", lambda port, available: port)
    monkeypatch.setattr(
        serial_handler_module,
        "discover_device",
        lambda preferred_port=None, baud=115200, allow_search=False, timeout=3.0: (
            None,
            None,
            None,
            "PermissionError(13, 'Access is denied.'): Port in use by another application or USB driver issue.",
        ),
    )

    result, message = handler.connect(port="COM4", baud=115200, auto_detect=False)

    assert result is False
    assert "Access is denied" in message
    assert "COM4" in message


def test_probe_handles_slow_boot_then_valid_reply(monkeypatch):
    """A healthy device that replies after a short boot delay should still be accepted within the probe window."""
    fake_module = type(sys)("fake_serial")
    fake_module.Serial = lambda: FakeSerial(boot_lines=["Booting..."], reply_lines=[VALID_DEVICE_JSON])
    monkeypatch.setattr(device_discovery, "serial", fake_module)
    monkeypatch.setattr(device_discovery.time, "sleep", lambda seconds: None)

    success, cable, metadata, error = device_discovery._probe_port("COM4", 115200, timeout=0.25)

    assert success is True
    assert metadata["device"] == "Digital Student Identification System"
    assert error == "OK"
    assert cable is not None
