"""Stable import paths for active and archived test fixtures."""

import atexit
import os
import shutil
import sys
import tempfile
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

# Keep the suite away from a developer's real data/attendance.db, exports and
# logs: several tests initialize the database, and some call destructive helpers
# such as clear_all_students(). This must run before anything imports
# core.config, which reads these variables at import time. Variables the
# developer already set are respected.
if "FINGERPRINT_DB_PATH" not in os.environ:
    _TEST_DATA_DIR = Path(tempfile.mkdtemp(prefix="dsis-tests-"))
    atexit.register(shutil.rmtree, _TEST_DATA_DIR, ignore_errors=True)
    os.environ["FINGERPRINT_DB_PATH"] = str(_TEST_DATA_DIR / "attendance.db")
    os.environ.setdefault("FINGERPRINT_EXPORT_FOLDER", str(_TEST_DATA_DIR / "exports"))
    os.environ.setdefault("FINGERPRINT_LOG_FOLDER", str(_TEST_DATA_DIR / "logs"))

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
