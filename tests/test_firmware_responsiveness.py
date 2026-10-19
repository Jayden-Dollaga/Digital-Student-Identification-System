"""Static checks for bounded, non-blocking host serial input in the maintained ESP32 sketch."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIRMWARE = ROOT / "firmware" / "ESP32_DSIS_AllInOne" / "ESP32_DSIS_AllInOne.ino"


def test_main_loop_does_not_wait_for_a_serial_line_timeout():
    source = FIRMWARE.read_text(encoding="utf-8")
    start = source.index("void loop()")
    end = source.index("//  COMMAND HANDLER", start)
    loop_body = source[start:end]

    assert "Serial.readStringUntil" not in loop_body
    assert "while (Serial.available() > 0)" in loop_body
    assert "SERIAL_COMMAND_MAX_LENGTH" in loop_body
    assert "serialCommandOverflow" in loop_body
