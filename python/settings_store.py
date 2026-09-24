import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from config import get_config

CONFIG = get_config()
SETTINGS_FILE = CONFIG.data_dir / "settings.json"
ADMIN_INITIALIZED_MARKER = CONFIG.data_dir / ".admin_initialized"

# Track stale port detection to avoid spam
_stale_port_last_checked: Dict[str, float] = {}
_STALE_PORT_CHECK_INTERVAL = 300  # Only check once every 5 minutes per port


def default_settings() -> Dict[str, Any]:
    return {
        "com_port": "",
        "baud_rate": CONFIG.baud_rate,
        "cooldown": CONFIG.cooldown_seconds,
        "theme": "dark",
        "auto_reconnect": True,
        "auto_detect_serial": True,
        # compact sidebar (icons-only) to save vertical space
        "compact_sidebar": False,
        # enable lightweight UI profiler (records timing of key UI events)
        "enable_profiler": False,
        # minimum AS608 confidence score (0-255) required to count a scan as a match
        "min_confidence": CONFIG.min_confidence,
        # write log output to a rotating file on disk in addition to console
        "log_to_file": CONFIG.log_to_file,
        # verbose DEBUG-level logging (noisier, useful for troubleshooting)
        "enable_debug_logging": CONFIG.enable_debug_logging,
        # last-known active user role, persisted ONLY for UI display continuity
        # (e.g. showing the right badge on next launch). This value is never
        # read for authorization decisions - see core.permissions, which is
        # backed exclusively by an in-memory session. Do not gate anything
        # off this field.
        "current_role": "guest",
        "rfid_payload_key": "",
        "rfid_app_key_hex": "",
        # minutes between automatic-backup due-checks (Settings > Backups)
        "auto_backup_interval_minutes": 25,
        # attendance time rules
        "time_in": "08:00",
        "time_out": "17:00",
        "early_threshold_minutes": 15,
        "late_threshold_minutes": 15,
        "absent_threshold_minutes": 0,
        "idle_timeout_minutes": 10,
        "auth": {},
        # Admin-managed exceptions to the normal school day, keyed by
        # "YYYY-MM-DD". Only exception dates are stored here - a normal
        # school day needs no entry at all. See core/attendance_calendar.py
        # for the entry shape and how each type is used.
        #   "2026-12-25": {"type": "holiday", "label": "Christmas Day"}
        #   "2026-11-14": {"type": "suspension", "label": "Typhoon signal #2"}
        #   "2026-08-30": {"type": "half_day", "label": "Foundation Day",
        #                   "time_in": "07:00", "time_out": "12:00"}
        "school_calendar": {},
        # Display name shown in the sidebar/header instead of the generic
        # "DSIS" label. Empty string = not yet set (first-run wizard step 4).
        "school_name": "",
        # Recurring no-class weekdays (Sunday=0 ... Saturday=6). These are
        # treated as school-wide exceptions for the calendar logic and are
        # saved as part of the schedule step.
        "school_weekdays_off": [],
        # First-run setup wizard progress. Password (step 1) isn't tracked
        # here - its own existence (auth.has_password_set) is the signal for
        # that step. These three track the REMAINING steps so the router
        # (Api.get_first_run_setup_status) knows exactly where to resume if
        # the app is closed mid-wizard, instead of restarting from step 1
        # every time.
        #   device_step_done: user either connected successfully, or
        #     explicitly clicked "I'll connect it later"
        #   schedule_step_done: user confirmed or adjusted the school
        #     schedule on the wizard's schedule step
        #   branding_step_done: user confirmed theme + school_name
        "setup_device_step_done": False,
        "setup_schedule_step_done": False,
        "setup_branding_step_done": False,
    }


def load_settings(path: str | Path | None = None) -> Dict[str, Any]:
    settings_path = Path(path or SETTINGS_FILE)
    if not settings_path.exists():
        return default_settings()

    try:
        with settings_path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
    except (json.JSONDecodeError, OSError):
        return default_settings()

    merged = default_settings()
    if isinstance(loaded, dict):
        merged.update({key: value for key, value in loaded.items() if key in merged})
    if not isinstance(merged.get("auth"), dict):
        merged["auth"] = {}
    return merged


def save_settings(settings: Dict[str, Any], path: str | Path | None = None) -> Path:
    settings_path = Path(path or SETTINGS_FILE)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    payload = default_settings()
    payload.update(settings)
    with settings_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return settings_path


def admin_initialization_marker_exists(path: str | Path | None = None) -> bool:
    return Path(path or ADMIN_INITIALIZED_MARKER).is_file()


def write_admin_initialization_marker(path: str | Path | None = None) -> Path:
    marker_path = Path(path or ADMIN_INITIALIZED_MARKER)
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text("initialized\n", encoding="utf-8")
    return marker_path


def cleanup_stale_port(port: str, available_ports: list[str]) -> Optional[str]:
    """Check if stored port still exists; return None (clear) if stale, port if still valid.
    
    Args:
        port: COM port to validate
        available_ports: List of currently available ports
    
    Returns:
        port if it exists in available_ports, None if stale
    """
    if not port or port in available_ports:
        return port
    
    # Port is stale (not in enumeration)
    key = f"stale_{port}"
    now = time.time()
    last_checked = _stale_port_last_checked.get(key, 0)
    
    if now - last_checked >= _STALE_PORT_CHECK_INTERVAL:
        _stale_port_last_checked[key] = now
        # Only log once every 5 minutes to reduce spam
        try:
            from core.logger import log
            log.info(
                "Stored COM port no longer available; will clear on next connection attempt",
                stored_port=port,
                available_ports=available_ports,
            )
        except ImportError:
            pass  # Logger not available during early init
    
    return None
