import re
import secrets
from typing import Optional, Tuple

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from settings_store import load_settings, save_settings

_CARD_BYTES = 48
_NONCE_BYTES = 12
_STUDENT_NO_BYTES = 17
_PAYLOAD_VERSION = 1


def _decode_rfid_key(encoded: str) -> Optional[bytes]:
    cleaned = str(encoded or "").strip()
    if len(cleaned) != 64:
        return None
    try:
        key = bytes.fromhex(cleaned)
    except ValueError:
        return None
    return key if len(key) == 32 else None


def get_or_create_rfid_app_key() -> bytes:
    settings = load_settings()
    key = _decode_rfid_key(settings.get("rfid_aes_gcm_key"))
    if key is None:
        key = secrets.token_bytes(32)
        settings["rfid_aes_gcm_key"] = key.hex().upper()
        save_settings(settings)
    return key


def _normalize_card_uid(card_uid: str) -> str:
    text = str(card_uid or "").strip().upper().replace("-", ":")
    if ":" not in text and len(text) % 2:
        raise ValueError("RFID card UID must contain complete bytes.")
    groups = text.split(":") if ":" in text else [text[index:index + 2] for index in range(0, len(text), 2)]
    if any(not re.fullmatch(r"[0-9A-F]{1,2}", group) for group in groups):
        raise ValueError("A valid RFID card UID is required.")
    if len(groups) not in {4, 7, 10}:
        raise ValueError("RFID card UID must contain 4, 7, or 10 bytes.")
    return ":".join(group.zfill(2) for group in groups)


def _payload_aad(card_uid: str) -> bytes:
    return b"DSIS-RFID" + bytes([_PAYLOAD_VERSION]) + _normalize_card_uid(card_uid).encode("ascii")


def encrypt_student_card_payload(fingerprint_id: int, student_no: str, card_uid: str) -> str:
    fingerprint_id = int(fingerprint_id)
    if not 1 <= fingerprint_id <= 127:
        raise ValueError("Fingerprint ID must be between 1 and 127.")
    text = str(student_no or "").strip().encode("utf-8")
    if not text or len(text) > _STUDENT_NO_BYTES:
        raise ValueError(f"Student number must be 1 to {_STUDENT_NO_BYTES} UTF-8 bytes.")
    plaintext = bytes([fingerprint_id, len(text)]) + text.ljust(_STUDENT_NO_BYTES, b"\x00")
    key = get_or_create_rfid_app_key()
    nonce = secrets.token_bytes(_NONCE_BYTES)
    aad = _payload_aad(card_uid)
    envelope = bytes([_PAYLOAD_VERSION]) + nonce + AESGCM(key).encrypt(nonce, plaintext, aad)
    if len(envelope) != _CARD_BYTES:
        raise ValueError("Encrypted RFID payload has an invalid size.")
    return envelope.hex().upper()


def decrypt_student_card_payload(data_hex: str, card_uid: str) -> Optional[Tuple[int, str]]:
    if not data_hex:
        return None
    try:
        raw = bytes.fromhex(str(data_hex).strip())
    except ValueError:
        return None
    if len(raw) != _CARD_BYTES or raw[0] != _PAYLOAD_VERSION:
        return None
    try:
        aad = _payload_aad(card_uid)
        plaintext = AESGCM(get_or_create_rfid_app_key()).decrypt(
            raw[1:1 + _NONCE_BYTES], raw[1 + _NONCE_BYTES:], aad
        )
    except (InvalidTag, ValueError):
        return None
    if len(plaintext) != 2 + _STUDENT_NO_BYTES:
        return None
    fingerprint_id, student_no_len = plaintext[:2]
    if not 1 <= fingerprint_id <= 127 or not 1 <= student_no_len <= _STUDENT_NO_BYTES:
        return None
    encoded = plaintext[2:2 + student_no_len]
    try:
        student_no = encoded.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if not student_no or not student_no.strip() or "\x00" in student_no:
        return None
    return fingerprint_id, student_no.strip()
