"""Regression test for "ESP32 won't connect" when the AS608 sensor fails to
initialize.

The firmware prints its identity JSON unprompted, immediately at boot -
*before* it calls finger.verifyPassword(). If that check fails (bad wiring,
sensor unpowered, loose connector), the firmware prints an error and drops
into an infinite while(1) loop that never reads Serial again. Previously,
_probe_port() only checked for a valid handshake in the reply to the ID?
command it sends *after* the boot-read phase - so a device stuck in that
loop always looked like "no handshake response", timing out the full probe
window, even though it had already announced exactly what device it was.

This asserts the probe now recognizes a valid handshake the moment it sees
it during the boot-read phase too, without needing a live round-trip.
"""

import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from core import device_discovery


class FakeSerialWithBootTiming:
    """Like the FakeSerial in test_serial_monitor_boot_banner.py, but
    in_waiting reflects whatever's left in the queue - so lines "arrive"
    during the initial boot-read drain loop instead of only being reachable
    from the post-handshake-write loop. This is what actually happens on
    real hardware: the identity JSON shows up well before Python ever gets
    around to writing "ID?".
    """

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
        self.write_calls = []

    def open(self):
        pass

    @property
    def in_waiting(self):
        return 1 if self._lines else 0

    def write(self, data):
        self.write_calls.append(data)

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


@pytest.fixture()
def fake_serial_module(monkeypatch):
    def _install(lines):
        fake_module = type(sys)("fake_serial")
        instance_holder = {}

        def _make_serial():
            instance = FakeSerialWithBootTiming(lines)
            instance_holder["instance"] = instance
            return instance

        fake_module.Serial = _make_serial
        monkeypatch.setattr(device_discovery, "serial", fake_module)
        monkeypatch.setattr(device_discovery.time, "sleep", lambda seconds: None)
        return instance_holder

    return _install


def test_connects_despite_sensor_failure_hang(fake_serial_module):
    """The exact scenario from the crash log: identity JSON prints, then the
    firmware reports a sensor error and goes silent forever. Connect must
    still succeed instead of timing out after 3+ seconds per port."""
    boot_sequence = [
        "========================================",
        "  AS608 All-in-One Fingerprint System",
        "========================================",
        IDENTITY_JSON,
        "ERROR: Sensor not found. Check wiring.",
        # Nothing else ever arrives - firmware is stuck in while(1).
    ]
    instance_holder = fake_serial_module(boot_sequence)

    success, cable, metadata, error = device_discovery._probe_port("COM4", 115200, timeout=3.0)

    assert success is True
    assert error == "OK"
    assert metadata["device"] == "Digital Student Identification System"

    # Must not have needed to send the ID? handshake at all - it already
    # had everything it needed from the unprompted boot output.
    assert instance_holder["instance"].write_calls == []

    # The sensor error itself should be visible in the captured boot text,
    # so the Serial Monitor shows the actual actionable problem instead of
    # a generic "no handshake response".
    captured = cable._probe_buffered_lines
    assert "ERROR: Sensor not found. Check wiring." in captured


def test_still_recognizes_healthy_boot_sequence_from_boot_phase(fake_serial_module):
    """Control case: a fully healthy device should also be recognized
    during the boot-read phase now (it doesn't need to wait for a live
    ID? round-trip either), and should still capture the rest of the
    banner up through READY."""
    boot_sequence = [
        IDENTITY_JSON,
        "Sensor found!",
        "Stored fingerprints: 4",
        "READY",
        READY_JSON,
    ]
    instance_holder = fake_serial_module(boot_sequence)

    success, cable, metadata, error = device_discovery._probe_port("COM4", 115200, timeout=3.0)

    assert success is True
    assert instance_holder["instance"].write_calls == []
    captured = cable._probe_buffered_lines
    assert "Sensor found!" in captured
    assert "Stored fingerprints: 4" in captured
    assert "READY" in captured


def test_falls_back_to_id_probe_when_nothing_arrives_during_boot(fake_serial_module):
    """If genuinely nothing shows up during the boot-read window (e.g. a
    non-ESP32 device, or one that only responds to explicit commands), the
    probe must still fall back to writing ID? and waiting for a reply -
    this fix must not break that existing path."""
    boot_sequence = []  # nothing during boot
    instance_holder = fake_serial_module(boot_sequence)

    success, cable, metadata, error = device_discovery._probe_port("COM4", 115200, timeout=0.5)

    assert success is False
    assert error == "no handshake response"
    # It should have at least tried writing the handshake command.
    assert len(instance_holder["instance"].write_calls) == 1
