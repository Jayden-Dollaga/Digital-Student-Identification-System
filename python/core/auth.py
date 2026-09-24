"""Password authentication primitives for the active v3 webview app.

There is no default/fallback administrator password. On a genuine first
launch, no "auth" record exists, so verify_password() fails closed for every
password. After initialization, losing the auth record is a recovery state,
not permission to create a replacement administrator password.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from typing import Any, Dict


PBKDF2_ITERATIONS = 310_000
PASSWORD_HASH_KEY = "password_hash"
PASSWORD_SALT_KEY = "password_salt"
MIN_PASSWORD_LENGTH = 8


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


def has_password_set(settings: Dict[str, Any]) -> bool:
    """Return True if settings already has a usable password hash record."""
    record = settings.get("auth")
    return isinstance(record, dict) and bool(record.get(PASSWORD_HASH_KEY)) and bool(
        record.get(PASSWORD_SALT_KEY)
    )


def validate_new_password(password: str, confirm_password: str) -> str | None:
    """Return an error message if the candidate password is unusable, else None."""
    if password != confirm_password:
        return "Passwords do not match."
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    return None


def set_initial_password(settings: Dict[str, Any], password: str) -> Dict[str, Any]:
    """Install the very first administrator password.

    Refuses to run if a password is already set - re-running first-run setup
    is not a valid way to reset a forgotten password (that would just be a
    second, quieter "admin"/"admin"-style bypass). Use change_admin_password
    (which requires the current password) for that instead.
    """
    if has_password_set(settings):
        raise ValueError("A password is already set; first-run setup cannot run again.")
    settings["auth"] = hash_password(password)
    return settings