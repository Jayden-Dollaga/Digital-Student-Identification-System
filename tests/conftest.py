"""Stable import paths for active and archived test fixtures."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PATHS = (
    ROOT / "python",
    ROOT / "tests" / "Prototype" / "Python",
)

for path in reversed(PATHS):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

from core import permissions


def grant_test_session_role(role: str = "admin", action: str = "enroll", timeout_seconds: float = 600.0) -> str:
    """Set the supported in-memory session role required for privileged hardware tests."""
    permissions.set_session_role(role, timeout_seconds)
    assert permissions.require_permission(action), (
        f"Session role '{role}' lacks permission '{action}'. "
        "Use the supported permissions.set_session_role() path before calling protected commands."
    )
    return permissions.get_current_role()


@pytest.fixture(autouse=True)
def reset_session_role_to_default():
    """Ensure privileged role state does not leak from one test into another."""
    yield
    permissions.set_session_role("guest", 600.0)
