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
        if "ESP32_DSIS_AllInOne" in str(sketch):
            assert '"CARD_ERASE"' in source
            assert "payloadText.length() != 96" in source
            assert "blockOffset < 3" in source
            assert "MIFARE_Read(block, verifyBuffer, &verifySize)" in source
            assert "memcmp(blockData, verifyBuffer, 16)" in source
            assert "rfid.PICC_WakeupA(atqa, &atqaSize)" in source
            assert "uidToString(&rfid.uid) != uidStr" in source
            assert "rfid.PICC_GetType(rfid.uid.sak)" in source
            assert "MFRC522::PICC_TYPE_MIFARE_1K" in source
            assert "Ultralight/Ultralight C is not supported" in source
            assert "!rfid.PICC_IsNewCardPresent() && !rfid.PICC_ReadCardSerial()" not in source
        assert 'normalized == "WIPE"' in source or 'input == "WIPE"' in source
        assert 'startsWith("DELETE:")' in source
