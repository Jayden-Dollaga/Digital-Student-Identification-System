import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON_ROOT = ROOT / "python"
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from gui.serial_troubleshooting import build_common_port_candidates
from gui.app import FingerprintApp


class DummyVar:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class DummyComboBox:
    def configure(self, **kwargs):
        self.kwargs = kwargs


class DummySerialHandler:
    def __init__(self, ports):
        self.ports = ports

    def list_available_ports(self):
        return self.ports


def test_common_port_candidates_include_common_values():
    candidates = build_common_port_candidates(["COM3", "COM4"])
    assert "COM3" in candidates
    assert "COM4" in candidates
    assert "COM5" in candidates
    assert "COM1" in candidates


def test_refresh_serial_ports_initial_does_not_trigger_auto_detect_again():
    app = object.__new__(FingerprintApp)
    app._closing = False
    app.auto_detect_serial = True
    app.serial_handler = DummySerialHandler(["COM3"])
    app.port_var = DummyVar()
    app.port_combobox = DummyComboBox()
    app.log_message = lambda msg: None

    def fail_auto_detect():
        raise AssertionError("auto detect should not be triggered from initial refresh")

    app.auto_detect_serial_on_startup = fail_auto_detect

    FingerprintApp.refresh_serial_ports(app, initial=True)

    assert app.port_var.get() == "COM3"
