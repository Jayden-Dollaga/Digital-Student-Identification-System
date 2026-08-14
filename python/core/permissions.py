"""Backend permission checks for role-gated actions.

Previously, role permissions (admin/teacher/guest) were only enforced by
enabling/disabling buttons in the Qt UI. The actual command functions in
core.commands (cmd_enroll, cmd_delete, cmd_wipe) would happily send the
command to the ESP32 regardless of the active role, since nothing checked
permissions below the UI layer. That meant anyone who could trigger those
functions directly - or who edited data/settings.json to set
"current_role": "admin" - could bypass the UI gating entirely.

This module gives core.commands (and anything else that needs it) a single
source of truth for "is this action allowed right now", based on the same
settings.json + USER_ROLES config the UI already uses.
"""

from __future__ import annotations

from typing import Optional

from config import get_config
from core.logger import log

CONFIG = get_config()


def get_current_role() -> str:
    """Return the currently active role key (e.g. 'admin', 'teacher', 'guest')."""
    try:
        from settings_store import load_settings
        settings = load_settings()
        return settings.get("current_role", CONFIG.default_user_role)
    except Exception:
        # If settings can't be read for any reason, fail safe to the
        # configured default rather than crashing the caller.
        return CONFIG.default_user_role


def has_permission(action: str, role_key: Optional[str] = None) -> bool:
    """Check whether the given (or current) role is allowed to perform `action`.

    Args:
        action: One of the permission strings defined in USER_ROLES,
            e.g. "enroll", "delete", "wipe", "export", "backup", "restore".
        role_key: Optional explicit role to check instead of the persisted
            current role. Mainly useful for testing.

    Returns:
        True if the role grants this permission, False otherwise (including
        for unknown roles - fail closed, not open).
    """
    role_key = role_key or get_current_role()
    role = CONFIG.user_roles.get(role_key)
    if not role:
        log.warning("Permission check against unknown role", role=role_key, action=action)
        return False
    return action in set(role.get("permissions", []))


def require_permission(action: str, role_key: Optional[str] = None) -> bool:
    """Like has_permission(), but also logs a warning when access is denied.

    Intended for use at the point where a privileged command is about to be
    sent, so denied attempts leave a trace instead of failing silently.
    """
    allowed = has_permission(action, role_key=role_key)
    if not allowed:
        log.warning(
            "Blocked action - current role lacks permission",
            action=action,
            role=role_key or get_current_role(),
        )
    return allowed
