from pathlib import Path
import sys
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

from core.serial_handler import SerialHandler


pytestmark = pytest.mark.unit


def test_adopted_serial_connection_notifies_firmware_host_connected():
    handler = SerialHandler()
    cable = MagicMock()
    cable.is_open = True
    handler.esp32 = cable

    handler._send_host_connected()

    cable.write.assert_called_once_with(
        b'{"type":"status","state":"HOST_CONNECTED"}\n'
    )

READY_STATUS = '{"type":"status","state":"READY"}'
HOST_CONNECTED = b'{"type":"status","state":"HOST_CONNECTED"}\n'


def _handler_with_line(line: str):
    handler = SerialHandler()
    cable = MagicMock()
    cable.is_open = True
    handler.esp32 = cable
    handler.connected = True
    handler._read_buffer = (line + "\n").encode("utf-8")
    return handler, cable


def test_boot_ready_status_reannounces_host_connected():
    """A rebooted board forgets HOST_CONNECTED; seeing its boot READY must restore it."""
    handler, cable = _handler_with_line(READY_STATUS)

    assert handler.read_line() == READY_STATUS

    cable.write.assert_called_once_with(HOST_CONNECTED)


def test_boot_ready_status_detection_tolerates_spacing():
    handler, cable = _handler_with_line('{"type": "status", "state": "READY"}')

    handler.read_line()

    cable.write.assert_called_once_with(HOST_CONNECTED)


@pytest.mark.parametrize(
    "line",
    [
        "READY",
        '{"type":"status","state":"SCAN_MODE"}',
        '{"type":"attendance","event":"match","id":1,"confidence":223}',
        "Stored fingerprints: 3",
    ],
)
def test_other_lines_do_not_trigger_host_announcement(line):
    handler, cable = _handler_with_line(line)

    assert handler.read_line() == line

    cable.write.assert_not_called()


def test_auto_detect_reconnect_reannounces_host_connected(monkeypatch):
    """The auto-detect reconnect branch used to adopt the port without announcing the host."""
    import types

    import core.serial_handler as serial_handler

    cable = MagicMock()
    cable.is_open = True
    monkeypatch.setattr(
        serial_handler,
        "CONFIG",
        types.SimpleNamespace(
            reconnect_base_delay=0,
            reconnect_max_retries=2,
            baud_rate=115200,
            auto_reconnect=True,
        ),
    )
    monkeypatch.setattr(
        serial_handler,
        "discover_device",
        lambda **kwargs: ("COM9", cable, {"device": "DSIS"}, "OK"),
    )

    handler = SerialHandler()
    handler._auto_detect_requested = True
    handler.reconnect_baud = 115200

    handler._reconnect_worker()

    assert handler.connected is True
    assert handler.reconnect_port == "COM9"
    cable.write.assert_called_once_with(HOST_CONNECTED)
