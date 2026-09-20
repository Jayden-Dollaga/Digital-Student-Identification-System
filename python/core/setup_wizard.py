"""First-run setup wizard router.

On every launch, the frontend asks get_first_run_setup_status() (see
gui_web.api) which step to show, if any. This module is the pure decision
function behind that - given the current settings and whether a password
exists yet, it returns the single next incomplete step, in a fixed order:

    1. password  (gated by auth.has_password_set - not a settings flag)
    2. device    (setup_device_step_done)
    3. schedule  (setup_schedule_step_done)
    4. branding  (setup_branding_step_done)
    None = wizard complete, show the normal Dashboard.

Steps 2-4 are individually flagged in settings.json as they're completed
(see settings_store.default_settings), so closing the app mid-wizard
resumes at the right step instead of restarting from step 1 - the
password step is the only one that can never be "lost", since its
completion is the existence of the password hash itself, not a flag that
could get out of sync with it.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

STEPS = ("password", "device", "schedule", "branding")


def get_next_step(settings: Mapping[str, Any], has_password: bool) -> Optional[str]:
    if not has_password:
        return "password"
    if not settings.get("setup_device_step_done"):
        return "device"
    if not settings.get("setup_schedule_step_done"):
        return "schedule"
    if not settings.get("setup_branding_step_done"):
        return "branding"
    return None


def is_setup_complete(settings: Mapping[str, Any], has_password: bool) -> bool:
    return get_next_step(settings, has_password) is None
