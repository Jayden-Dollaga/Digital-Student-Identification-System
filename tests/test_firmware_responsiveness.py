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


def _source() -> str:
    return FIRMWARE.read_text(encoding="utf-8")


def test_card_keycheck_is_serviced_in_command_mode():
    source = _source()
    loop_body = source[source.index("void loop()"):source.index("//  COMMAND HANDLER")]

    assert "pendingCardWrite.length() > 0 || pendingCardErase || pendingKeyCheck" in loop_body
    # STOP and DELETE must not leave a stale key check armed.
    assert "pendingKeyCheck = false;" in source[source.index('normalized == "STOP"'):source.index("// ── LIST")]


def test_help_command_exists_and_enroll_uses_parsed_payload():
    source = _source()
    handler = source[source.index("void handleCommand"):source.index("//  ENROLL HELPERS")]

    assert 'normalized == "HELP"' in handler
    assert 'input.startsWith("ENROLL:")' not in handler
    assert 'normalized.startsWith("ENROLL:")' in handler
    assert "payload.toInt()" in handler


def test_scan_finger_cooldown_is_non_blocking():
    source = _source()
    scan_finger = source[source.index("void scanFinger()"):source.index("//  RFID CARD")]

    assert "delay(" not in scan_finger
    assert "fingerCooldownMs" in scan_finger


def test_enrollment_waits_are_bounded_and_leave_the_led_clean():
    source = _source()
    enroll = source[source.index("void enrollFinger"):source.index("//  SCAN (Attendance Mode)")]

    assert enroll.count("enrollWaitTimedOut(") >= 3
    assert "void runEnrollment(int id)" in enroll
    assert "enrolling = false;" in enroll
    assert "readStringUntil" not in enroll
