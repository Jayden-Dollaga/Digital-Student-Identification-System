"""Backend permission checks for role-gated actions.

Previously, role permissions (admin/teacher/guest) were only enforced by
enabling/disabling buttons in the Qt UI. The actual command functions in
core.commands (cmd_enroll, cmd_delete, cmd_wipe) would happily send the
command to the ESP32 regardless of the active role, since nothing checked
permissions below the UI layer. That meant anyone who could trigger those
functions directly - or who edited data/settings.json to set
"current_role": "admin" - could bypass the UI gating entirely.

This module gives core.commands (and anything else that needs it) a single
source of truth for "is this action allowed right now".

IMPORTANT: the current role is ALWAYS the in-memory session role set via
set_session_role() (established at password login, expired by idle timeout).
settings.json is never consulted for authorization - it only stores the
*password hash* (checked by core.auth) and, separately, a "current_role"
field that exists purely for display/UX continuity in the settings page.
Editing that field by hand does nothing: any code path that calls
get_current_role() before a session has been established (e.g. a script
that imports this module directly without going through gui_web.api.Api)
gets "guest", never an escalated role read from disk.
"""

from __future__ import annotations

import time
from typing import Optional

from config import get_config
from core.logger import log

CONFIG = get_config()
ROLE_LEVELS = {"guest": 0, "teacher": 1, "admin": 2}
ATTENDANCE_TIME_RULES_PERMISSION = "admin"
_session_role: Optional[str] = None
_session_expires_at: Optional[float] = None
_session_timeout_seconds = 600.0


def set_session_role(role_key: Optional[str], timeout_seconds: Optional[float] = None) -> None:
    """Set the in-memory role used by the active v3 API session."""
    global _session_role, _session_expires_at, _session_timeout_seconds
    _session_role = role_key if role_key in ROLE_LEVELS else "guest"
    if timeout_seconds is not None:
        _session_timeout_seconds = max(0.01, float(timeout_seconds))
    _session_expires_at = time.monotonic() + _session_timeout_seconds if _session_role != "guest" else None


def touch_session() -> str:
    """Refresh the authenticated session and return its effective role."""
    role = get_current_role()
    if role != "guest":
        global _session_expires_at
        _session_expires_at = time.monotonic() + _session_timeout_seconds
    return role


def get_current_role() -> str:
    """Return the currently active role key (e.g. 'admin', 'teacher', 'guest').

    This is ALWAYS derived from the in-memory session, never from
    settings.json. If no session has been established yet (e.g. this is
    called before gui_web.api.Api has initialized one, or from a script
    that never calls set_session_role()), the effective role is "guest" -
    full stop. There is no disk-backed escalation path.
    """
    global _session_role
    if _session_role is None:
        # No session established yet anywhere in this process - guest.
        return "guest"
    if _session_expires_at is not None and time.monotonic() >= _session_expires_at:
        set_session_role("guest")
    return _session_role


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


def has_role_permission(current_role: str, required_role: str) -> bool:
    """Return whether a role meets the required role level."""
    return ROLE_LEVELS.get(current_role, -1) >= ROLE_LEVELS.get(required_role, 99)


def require_role(required_role: str, current_role: Optional[str] = None) -> bool:
    role = current_role or get_current_role()
    allowed = has_role_permission(role, required_role)
    if not allowed:
        log.warning("Blocked role-gated action", required_role=required_role, role=role)
    return allowed


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
