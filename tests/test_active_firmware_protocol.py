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
            detector = (ROOT / "firmware" / "ESP32_DSIS_AllInOne" / "src" / "rfid" / "CardDetector.cpp").read_text(encoding="utf-8")
            classic = (ROOT / "firmware" / "ESP32_DSIS_AllInOne" / "src" / "rfid" / "ClassicAdapter.cpp").read_text(encoding="utf-8")
            type2 = (ROOT / "firmware" / "ESP32_DSIS_AllInOne" / "src" / "rfid" / "Type2Adapter.cpp").read_text(encoding="utf-8")
            assert '"CARD_ERASE"' in source
            assert "payloadText.length() != 96" in source
            assert "offset < 3" in classic
            assert "MIFARE_Read(firstBlock + offset, verifyBuffer, &verifySize)" in classic
            assert "memcmp(payload + offset * 16, verifyBuffer, 16)" in classic
            assert "writeClassicPayload(rfid, RFID_BLOCK_NUM, payloadBuffer)" in source
            assert "readClassicPayload(rfid, RFID_BLOCK_NUM, payloadBuffer)" in source
            assert "reader.PICC_WakeupA(atqa, &atqaSize)" in classic
            assert "sameUid(reader.uid, originalUid)" in classic
            assert "RFID_KEY_CANDIDATES" not in source
            assert "RFID_KEY_CANDIDATES" in classic
            assert "detectRfidCard(rfid)" in source
            assert "PICC_GetType(reader.uid.sak)" in detector
            for card_type in ("PICC_TYPE_MIFARE_MINI", "PICC_TYPE_MIFARE_1K", "PICC_TYPE_MIFARE_4K"):
                assert card_type in detector
            assert '"TYPE2_144B_AMBIGUOUS"' in detector
            assert '"NTAG_215"' in detector and '"NTAG_216"' in detector
            assert "pageBuffer[3] != 0" in detector
            assert "MIFARE_Ultralight_Write" in type2
            assert "readType2Payload(rfid, payloadBuffer)" in source
            assert "writeType2Payload(rfid, payloadBuffer)" in source
            assert "operation" in source and "verified" in source
            assert "erase_verified" in source and "write_verified" in source
            classic = (ROOT / "firmware" / "ESP32_DSIS_AllInOne" / "src" / "rfid" / "ClassicAdapter.cpp").read_text(encoding="utf-8")
            assert "RFID_KEY_CANDIDATES" not in source
            assert "RFID_KEY_CANDIDATES" in classic
            assert "!rfid.PICC_IsNewCardPresent() && !rfid.PICC_ReadCardSerial()" not in source
        assert 'normalized == "WIPE"' in source or 'input == "WIPE"' in source
        assert 'startsWith("DELETE:")' in source
