from pathlib import Path

import pytest


pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[1]


def test_firmware_destructive_commands_require_host_connection():
    sketches = (
        ROOT / "firmware" / "ESP32_DSIS_AllInOne" / "ESP32_DSIS_AllInOne.ino",
        ROOT / "firmware" / "ESP32_Fingerprint_AllInOne" / "ESP32_Fingerprint_AllInOne.ino",
    )

    for sketch in sketches:
        source = sketch.read_text(encoding="utf-8")
        assert "bool hostConnected = false;" in source
        assert 'status == "HOST_CONNECTED"' in source
        assert 'status == "HOST_DISCONNECTED"' in source
        assert '"ERROR: Host connection required for this command."' in source
        assert 'normalized == "WIPE"' in source or 'input == "WIPE"' in source
        assert 'startsWith("DELETE:")' in source
