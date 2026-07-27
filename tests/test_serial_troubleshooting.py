import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOT = ROOT / "python"
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from gui.serial_troubleshooting import build_serial_troubleshooting_message


def test_troubleshooting_message_mentions_common_drivers_and_steps():
    message = build_serial_troubleshooting_message([])
    assert "CP210x" in message
    assert "CH340" in message
    assert "Device Manager" in message
    assert "Refresh" in message
