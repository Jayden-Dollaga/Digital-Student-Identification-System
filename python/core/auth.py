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
MIN_PBKDF2_ITERATIONS = 100_000
MAX_PBKDF2_ITERATIONS = 1_000_000
PASSWORD_SALT_BYTES = 16
PASSWORD_DIGEST_BYTES = 32
PASSWORD_HASH_KEY = "password_hash"
PASSWORD_SALT_KEY = "password_salt"
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 1024


def hash_password(password: str) -> Dict[str, Any]:
    if not isinstance(password, str):
        raise ValueError("Password must be text.")
    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValueError(f"Password must be no longer than {MAX_PASSWORD_LENGTH} characters.")
    salt = secrets.token_bytes(PASSWORD_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return {
        PASSWORD_SALT_KEY: base64.b64encode(salt).decode("ascii"),
        PASSWORD_HASH_KEY: base64.b64encode(digest).decode("ascii"),
        "iterations": PBKDF2_ITERATIONS,
    }


def verify_password(password: str, record: Dict[str, Any]) -> bool:
    """Verify an untrusted persisted hash record without unbounded CPU work."""
    if (
        not isinstance(password, str)
        or len(password) > MAX_PASSWORD_LENGTH
        or not isinstance(record, dict)
    ):
        return False
    try:
        salt_text = record[PASSWORD_SALT_KEY]
        hash_text = record[PASSWORD_HASH_KEY]
        # Canonical base64 lengths are fixed for these fixed-size values.
        # Check before decoding so a huge malformed local field can't allocate
        # excessive memory during login.
        if (
            not isinstance(salt_text, str)
            or len(salt_text) != 24
            or not isinstance(hash_text, str)
            or len(hash_text) != 44
        ):
            return False
        salt = base64.b64decode(salt_text, validate=True)
        expected = base64.b64decode(hash_text, validate=True)
        iterations = int(record.get("iterations", PBKDF2_ITERATIONS))
        if not MIN_PBKDF2_ITERATIONS <= iterations <= MAX_PBKDF2_ITERATIONS:
            return False
        if len(salt) != PASSWORD_SALT_BYTES or len(expected) != PASSWORD_DIGEST_BYTES:
            return False
    except (KeyError, TypeError, ValueError, OverflowError):
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


def has_password_material(settings: Dict[str, Any]) -> bool:
    """Return True if settings contain any non-empty persisted verifier material.

    A partial/malformed verifier must trigger recovery, not first-run setup;
    otherwise a broken existing install could be silently re-enrolled.
    """
    record = settings.get("auth")
    if not isinstance(record, dict):
        return False
    return any(
        record.get(key) not in (None, "")
        for key in (PASSWORD_HASH_KEY, PASSWORD_SALT_KEY)
    )


def has_password_set(settings: Dict[str, Any]) -> bool:
    """Return True only if the stored password verifier is structurally usable."""
    record = settings.get("auth")
    if not isinstance(record, dict):
        return False
    try:
        salt_text = record[PASSWORD_SALT_KEY]
        hash_text = record[PASSWORD_HASH_KEY]
        if (
            not isinstance(salt_text, str)
            or len(salt_text) != 24
            or not isinstance(hash_text, str)
            or len(hash_text) != 44
        ):
            return False
        salt = base64.b64decode(salt_text, validate=True)
        digest = base64.b64decode(hash_text, validate=True)
        iterations = int(record.get("iterations", PBKDF2_ITERATIONS))
    except (KeyError, TypeError, ValueError, OverflowError):
        return False
    return (
        len(salt) == PASSWORD_SALT_BYTES
        and len(digest) == PASSWORD_DIGEST_BYTES
        and MIN_PBKDF2_ITERATIONS <= iterations <= MAX_PBKDF2_ITERATIONS
    )


def validate_new_password(password: str, confirm_password: str) -> str | None:
    """Return an error message if the candidate password is unusable, else None."""
    if not isinstance(password, str) or not isinstance(confirm_password, str):
        return "Password fields must be text."
    if password != confirm_password:
        return "Passwords do not match."
    if len(password) > MAX_PASSWORD_LENGTH:
        return f"Password must be no longer than {MAX_PASSWORD_LENGTH} characters."
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
    if has_password_material(settings):
        raise ValueError(
            "Administrator password material already exists; first-run setup cannot overwrite it. "
            "Use the administrator recovery process."
        )
    settings["auth"] = hash_password(password)
    return settings