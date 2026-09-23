import secrets
from typing import Optional, Tuple

from settings_store import load_settings, save_settings

_CARD_BYTES = 16


def _decode_rfid_key(encoded: str) -> Optional[bytes]:
    cleaned = str(encoded or "").strip()
    if len(cleaned) != 32:
        return None
    try:
        key = bytes.fromhex(cleaned)
    except ValueError:
        return None
    return key if len(key) == _CARD_BYTES else None


def get_or_create_rfid_app_key() -> bytes:
    settings = load_settings()
    for key_name in ("rfid_payload_key", "rfid_app_key_hex"):
        key = _decode_rfid_key(settings.get(key_name))
        if key is not None:
            settings["rfid_payload_key"] = key.hex().upper()
            settings["rfid_app_key_hex"] = settings["rfid_payload_key"]
            save_settings(settings)
            return key

    key = secrets.token_bytes(_CARD_BYTES)
    settings["rfid_payload_key"] = key.hex().upper()
    settings["rfid_app_key_hex"] = settings["rfid_payload_key"]
    save_settings(settings)
    return key


def _xor_block(data: bytes, key: bytes) -> bytes:
    if len(data) != _CARD_BYTES or len(key) != _CARD_BYTES:
        raise ValueError("RFID block payloads must be exactly 16 bytes.")
    return bytes(
        byte ^ key[idx] ^ ((idx * 7 + 1) & 0xFF)
        for idx, byte in enumerate(data)
    )


def encrypt_student_card_payload(fingerprint_id: int, student_no: str) -> str:
    text = str(student_no or "").strip().encode("utf-8")[:14]
    block = bytearray(16)
    block[0] = 1
    block[1] = int(fingerprint_id) & 0xFF
    if len(text) < 14:
        block[2 : 2 + len(text)] = text
        block[2 + len(text) : 16] = b"\x00" * (14 - len(text))
    else:
        block[2:16] = text[:14]
    key = get_or_create_rfid_app_key()
    return _xor_block(bytes(block), key).hex().upper()


def decrypt_student_card_payload(data_hex: str) -> Optional[Tuple[int, str]]:
    if not data_hex:
        return None
    try:
        raw = bytes.fromhex(str(data_hex).strip())
    except ValueError:
        return None
    if len(raw) != _CARD_BYTES:
        return None
    key = get_or_create_rfid_app_key()
    block = _xor_block(raw, key)
    if len(block) != _CARD_BYTES or block[0] != 1:
        return None
    fingerprint_id = int(block[1])
    encoded = bytes(block[2:16]).split(b"\x00", 1)[0]
    try:
        student_no = encoded.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if not student_no or not student_no.strip():
        return None
    return fingerprint_id, student_no.strip()
