"""Password authentication primitives for the active v3 webview app."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from typing import Any, Dict, cast


DEFAULT_ADMIN_PASSWORD = "dsis-admin"
PBKDF2_ITERATIONS = 310_000
PASSWORD_HASH_KEY = "password_hash"
PASSWORD_SALT_KEY = "password_salt"


def hash_password(password: str) -> Dict[str, Any]:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return {
        PASSWORD_SALT_KEY: base64.b64encode(salt).decode("ascii"),
        PASSWORD_HASH_KEY: base64.b64encode(digest).decode("ascii"),
        "iterations": PBKDF2_ITERATIONS,
    }


def verify_password(password: str, record: Dict[str, Any]) -> bool:
    try:
        salt = base64.b64decode(record[PASSWORD_SALT_KEY], validate=True)
        expected = base64.b64decode(record[PASSWORD_HASH_KEY], validate=True)
        iterations = int(record.get("iterations", PBKDF2_ITERATIONS))
        if iterations < 100_000:
            return False
    except (KeyError, TypeError, ValueError):
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


def ensure_password_record(settings: Dict[str, Any]) -> Dict[str, Any]:
    record = settings.get("auth")
    typed_record = cast(Dict[str, Any], record)
    if isinstance(record, dict) and verify_password(DEFAULT_ADMIN_PASSWORD, typed_record):
        return settings
    if not isinstance(record, dict) or not typed_record.get(PASSWORD_HASH_KEY):
        settings["auth"] = hash_password(DEFAULT_ADMIN_PASSWORD)
    return settings