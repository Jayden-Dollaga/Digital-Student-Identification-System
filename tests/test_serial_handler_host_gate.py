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