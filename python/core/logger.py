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
from pathlib import Path
from typing import Any, Dict, Optional

from config import get_config

CONFIG = get_config()

LOG_LEVEL = getattr(logging, CONFIG.log_level.upper(), logging.INFO)
LOG_NAME = "FingerprintAttendance"

if CONFIG.log_to_file:
    log_dir = Path(CONFIG.log_folder)
    log_dir.mkdir(parents=True, exist_ok=True)
    LOG_FILE = log_dir / CONFIG.log_file_name
else:
    LOG_FILE = None


class AppFormatter(logging.Formatter):
    """Formatter supporting simple structured message payloads."""

    def format(self, record: logging.LogRecord) -> str:
        original_msg = record.msg
        original_args = record.args
        try:
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

    def _format_structured(self, payload: Dict[str, Any]) -> str:
        return " | ".join(f"{key}={value}" for key, value in payload.items())


def _configure_logger() -> logging.Logger:
    logger = logging.getLogger(LOG_NAME)
    logger.setLevel(LOG_LEVEL)
    logger.handlers.clear()
    logger.propagate = False

    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(
        AppFormatter("%(asctime)s [%(levelname)-8s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    )
    logger.addHandler(console_handler)

    if LOG_FILE is not None:
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=str(LOG_FILE),
            when=CONFIG.log_rotation_when,
            interval=CONFIG.log_rotation_interval,
            backupCount=CONFIG.log_rotation_backup_count,
            encoding="utf-8",
            utc=False,
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            AppFormatter("%(asctime)s [%(levelname)-8s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        )
        logger.addHandler(file_handler)

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
