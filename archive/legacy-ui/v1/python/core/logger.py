###############################################################################
#  logger.py
#  AS608 Fingerprint Attendance System
#
#  Centralized logging configuration and runtime logger provider.
#  Uses the standard library logging module with optional rotating file
#  output and structured message formatting.
###############################################################################

import logging
import logging.handlers
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from config import get_config

CONFIG = get_config()

LOG_LEVEL = getattr(logging, CONFIG.log_level.upper(), logging.INFO)
LOG_NAME = "FingerprintAttendance"

if CONFIG.log_to_file:
    log_dir = Path(CONFIG.log_folder)
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        # One fresh, timestamped file per run (matches the backup naming
        # style) instead of a single fixed-name file that gets appended to
        # or rotated only at midnight - so each launch has its own log.
        stem = Path(CONFIG.log_file_name).stem
        suffix = Path(CONFIG.log_file_name).suffix or ".log"
        run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        LOG_FILE = log_dir / f"{stem}_{run_timestamp}{suffix}"
    except Exception:
        # If the log directory can't even be created (permissions, a weird
        # path, etc.) fall back to console-only rather than crashing the
        # whole app before the window can show.
        LOG_FILE = None
else:
    LOG_FILE = None


class AppFormatter(logging.Formatter):
    """Formatter supporting simple structured message payloads."""

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        if datefmt and "%f" in datefmt:
            timestamp = time.localtime(record.created)
            microsecond = int(record.msecs * 1000)
            fmt = datefmt.replace("%f", "{microsecond:06d}")
            return time.strftime(fmt, timestamp).format(microsecond=microsecond)
        return super().formatTime(record, datefmt)

    def format(self, record: logging.LogRecord) -> str:
        original_msg = record.msg
        original_args = record.args
        original_source = getattr(record, "source", None)
        try:
            if original_source is None:
                record.source = self._derive_source(record)

            if isinstance(record.msg, dict):
                record.msg = self._format_structured(record.msg)
                record.args = ()
            else:
                structured = getattr(record, "structured", None)
                if isinstance(structured, dict):
                    record.msg = f"{record.getMessage()} | {self._format_structured(structured)}"
                    record.args = ()
            return super().format(record)
        finally:
            record.msg = original_msg
            record.args = original_args
            if original_source is None:
                try:
                    delattr(record, "source")
                except Exception:
                    pass
            else:
                record.source = original_source

    def _derive_source(self, record: logging.LogRecord) -> str:
        module = (getattr(record, "module", "") or "").lower()
        if module.startswith("serial_handler") or module.startswith("device_discovery"):
            return "SERIAL"
        if module.startswith("attendance"):
            return "ATTENDANCE"
        if module.startswith("database"):
            return "DATABASE"
        if module.startswith("gui_qt") or module.startswith("main_window") or module.startswith("serial_worker"):
            return "GUI"
        if module.startswith("logger"):
            return "SYSTEM"
        if module.startswith("main"):
            return "SYSTEM"
        if module:
            return module.upper()
        return "SYSTEM"

    def _format_structured(self, payload: Dict[str, Any]) -> str:
        return " | ".join(f"{key}={value}" for key, value in payload.items())


def _prune_old_logs(log_dir: Path, keep: int) -> None:
    """Delete old per-run log files, keeping only the most recent `keep`.

    Runs once at startup right after the new file's handler is attached.
    Mirrors the intent of the old TimedRotatingFileHandler's backupCount,
    just applied per-run instead of per-day.
    """
    if keep <= 0:
        return
    try:
        pattern = f"{Path(CONFIG.log_file_name).stem}_*{Path(CONFIG.log_file_name).suffix or '.log'}"
        existing = sorted(log_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
        for stale_file in existing[keep:]:
            stale_file.unlink(missing_ok=True)
    except Exception:
        # Cleanup failures should never block the app from starting.
        pass


def _configure_logger() -> logging.Logger:
    logger = logging.getLogger(LOG_NAME)
    logger.setLevel(LOG_LEVEL)
    logger.handlers.clear()
    logger.propagate = False

    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(
        AppFormatter("%(asctime)s | %(levelname)-7s | %(source)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S.%f")
    )
    logger.addHandler(console_handler)

    if LOG_FILE is not None:
        try:
            file_handler = logging.FileHandler(
                filename=str(LOG_FILE),
                encoding="utf-8",
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(
                AppFormatter("%(asctime)s | %(levelname)-7s | %(source)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S.%f")
            )
            logger.addHandler(file_handler)

            _prune_old_logs(LOG_FILE.parent, keep=CONFIG.log_rotation_backup_count)
        except Exception as exc:
            # This used to crash the entire app at import time (before
            # sys.excepthook was even installed) whenever the log file was
            # transiently locked - e.g. an antivirus scan grabbing the
            # freshly-created file, or a previous instance of this app not
            # having fully released its handle yet. That produced exactly
            # the "closes immediately, works the 2nd time" behavior. Now we
            # just fall back to console-only logging instead of dying.
            logger.warning(f"File logging unavailable, continuing with console-only logging: {exc}")

    return logger


LOG = _configure_logger()

SUCCESS_LEVEL = 25
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")


def _log_with_structured(level: int, message: Any, **kwargs: Any) -> None:
    extra: Dict[str, Any] = {}
    if kwargs:
        extra["structured"] = kwargs

    if isinstance(message, dict):
        LOG.log(level, message, extra=extra)
    else:
        LOG.log(level, str(message), extra=extra)

    for handler in LOG.handlers:
        if hasattr(handler, "flush"):
            handler.flush()


def debug(message: Any, **kwargs: Any) -> None:
    _log_with_structured(logging.DEBUG, message, **kwargs)


def info(message: Any, **kwargs: Any) -> None:
    _log_with_structured(logging.INFO, message, **kwargs)


def success(message: Any, **kwargs: Any) -> None:
    _log_with_structured(SUCCESS_LEVEL, message, **kwargs)


def warning(message: Any, **kwargs: Any) -> None:
    _log_with_structured(logging.WARNING, message, **kwargs)


def error(message: Any, **kwargs: Any) -> None:
    _log_with_structured(logging.ERROR, message, **kwargs)


def critical(message: Any, **kwargs: Any) -> None:
    _log_with_structured(logging.CRITICAL, message, **kwargs)


def exception(message: Any, **kwargs: Any) -> None:
    extra: Dict[str, Any] = {}
    if kwargs:
        extra["structured"] = kwargs
        LOG.exception(message, extra=extra)
    else:
        LOG.exception(message)


class LoggerProxy:
    """Simple proxy to preserve the previous log object interface."""

    def debug(self, message: Any, **kwargs: Any) -> None:
        debug(message, **kwargs)

    def info(self, message: Any, **kwargs: Any) -> None:
        info(message, **kwargs)

    def success(self, message: Any, **kwargs: Any) -> None:
        success(message, **kwargs)

    def warning(self, message: Any, **kwargs: Any) -> None:
        warning(message, **kwargs)

    def error(self, message: Any, **kwargs: Any) -> None:
        error(message, **kwargs)

    def critical(self, message: Any, **kwargs: Any) -> None:
        critical(message, **kwargs)

    def exception(self, message: Any, **kwargs: Any) -> None:
        exception(message, **kwargs)


log = LoggerProxy()