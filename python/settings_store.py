import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from config import get_config

CONFIG = get_config()
SETTINGS_FILE = CONFIG.data_dir / "settings.json"

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
        # active user role: gates access to destructive/admin-only actions in the UI
        "current_role": CONFIG.default_user_role,
        # minutes between automatic-backup due-checks (Settings > Backups)
        "auto_backup_interval_minutes": 25,
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
    return merged


def save_settings(settings: Dict[str, Any], path: str | Path | None = None) -> Path:
    settings_path = Path(path or SETTINGS_FILE)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    payload = default_settings()
    payload.update(settings)
    with settings_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return settings_path


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
