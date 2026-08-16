"""Regression test for the "Serial Monitor doesn't show the full boot banner" bug.

_probe_port() used to return the instant it saw the device's identity JSON.
But the firmware prints that JSON *first*, then "Sensor found!", "Stored
fingerprints: N", the full command list, and finally a READY status line -
all of which was being thrown away because the function returned before any
of it arrived. This asserts the trailing boot text now gets captured too.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from core import device_discovery


class FakeSerial:
    """Minimal stand-in for pyserial's Serial, replaying a canned boot sequence."""

    def __init__(self, lines):
        self._lines = list(lines)
        self.port = None
        self.baudrate = None
        self.timeout = None
        self.dsrdtr = None
        self.rtscts = None
        self.xonxoff = None
        self.dtr = None
        self.rts = None

    def open(self):
        pass

    @property
    def in_waiting(self):
        # Nothing shows up before the handshake write in this simulation -
        # every line arrives via readline() calls in the post-write loop,
        # same as the real-world timing that triggered the bug.
        return 0

    def write(self, data):
        pass

    def flush(self):
        pass

    def reset_output_buffer(self):
        pass

    def readline(self):
        if self._lines:
            return (self._lines.pop(0) + "\n").encode("utf-8")
        return b""

    def close(self):
        pass


IDENTITY_JSON = (
    '{"device": "Digital Student Identification System", "board": "ESP32", '
    '"firmware": "1.0", "sensor": "AS608", "protocol": 1, "serial_number": "106365625798428"}'
)
READY_JSON = '{"type":"status","state":"READY"}'

BOOT_SEQUENCE = [
    IDENTITY_JSON,
    "Sensor found!",
    "Stored fingerprints: 4",
    "",
    "Commands (line ending must be set to Newline):",
    "  ENROLL      Enroll finger using next free ID",
    "READY",
    READY_JSON,
]


@pytest.fixture()
def fake_serial_module(monkeypatch):
    fake_module = type(sys)("fake_serial")
    fake_module.Serial = lambda: FakeSerial(BOOT_SEQUENCE)
    monkeypatch.setattr(device_discovery, "serial", fake_module)
    # Skip the real 1.0s boot-wait sleep so the test runs instantly.
    monkeypatch.setattr(device_discovery.time, "sleep", lambda seconds: None)
    return fake_module


def test_probe_captures_full_boot_banner_not_just_identity_json(fake_serial_module):
    success, cable, metadata, error = device_discovery._probe_port("COM4", 115200, timeout=3.0)

    assert success is True
    assert error == "OK"
    assert metadata["device"] == "Digital Student Identification System"

    captured = cable._probe_buffered_lines
    # The lines that used to get thrown away because the function returned
    # the instant it saw the identity JSON:
    assert "Sensor found!" in captured
    assert "Stored fingerprints: 4" in captured
    assert "Commands (line ending must be set to Newline):" in captured
    assert "READY" in captured


def test_probe_stops_promptly_once_ready_status_seen(fake_serial_module):
    """Shouldn't burn the full 1.5s trailing grace window once READY arrives."""
    import time

    start = time.time()
    success, cable, metadata, error = device_discovery._probe_port("COM4", 115200, timeout=3.0)
    elapsed = time.time() - start

    assert success is True
    # Generous ceiling - this should return almost immediately since the
    # canned sequence ends right after the READY status line, not after
    # burning the full grace window.
    assert elapsed < 1.0
