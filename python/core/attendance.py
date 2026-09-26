"""Attendance processing utilities for turning ESP32 output into structured scans.

The processor sits between the serial layer and the persistence layer, applying
cooldown rules and confidence-based logic so the rest of the app can work with
stable scan outcomes.
"""

###############################################################################
#  attendance.py
#  AS608 Fingerprint Attendance System
#
#  Scan processing and duplicate protection logic.
#  Sits between serial_handler (reads raw data) and database (logs it).
###############################################################################

import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypedDict

from config import get_config
from core.database import get_all_students, get_student, get_student_by_card_uid, log_attendance, normalize_card_uid, StudentRow
from core.logger import log
from core.rfid_card import decrypt_student_card_payload
from core.utils import parse_json_line

CONFIG = get_config()
COOLDOWN_SECONDS = CONFIG.cooldown_seconds
MIN_CONFIDENCE = CONFIG.min_confidence


class ScanResult(TypedDict, total=False):
    fingerprint_id: int
    confidence: int
    status: Optional[str]
    timestamp: datetime
    logged: bool
    reason: Optional[str]
    method: str
    uid: Optional[str]
    data: Optional[str]
    card_type: Optional[str]


@dataclass
class ScanOutcome:
    fingerprint_id: int
    confidence: int
    status: Optional[str]
    timestamp: datetime
    logged: bool
    reason: Optional[str] = None
    method: str = "fingerprint"
    uid: Optional[str] = None
    data: Optional[str] = None
    card_type: Optional[str] = None

    def to_dict(self) -> ScanResult:
        return asdict(self)


class AttendanceProcessor:
    def __init__(
        self,
        cooldown_seconds: int = COOLDOWN_SECONDS,
        min_confidence: int = MIN_CONFIDENCE,
        log_attendance_fn: Callable[..., None] = log_attendance,
        student_lookup_fn: Callable[[int], Optional[StudentRow]] = get_student,
        all_students_fn: Callable[[], List[StudentRow]] = get_all_students,
        card_lookup_fn: Callable[[str], Optional[StudentRow]] = get_student_by_card_uid,
    ):
        self.last_scan: Dict[int, datetime] = {}
        self.current_id: Optional[int] = None
        self.cooldown_seconds = cooldown_seconds
        self.min_confidence = min_confidence
        self._log_attendance = log_attendance_fn
        self._student_lookup = student_lookup_fn
        self._all_students = all_students_fn
        self._card_lookup = card_lookup_fn

    def process_line(self, line: str) -> Optional[ScanResult]:
        """
        Process a single ESP32 output line.
        Returns a structured scan result dict when a scan is completed.
        """
        if not isinstance(line, str):
            return None

        line = line.strip()
        if not line:
            return None

        parsed_json = parse_json_line(line)
        if parsed_json is not None:
            if parsed_json.get("type") == "attendance":
                event = parsed_json.get("event")
                if event == "match":
                    fingerprint_id = self._parse_json_int(parsed_json.get("id"))
                    confidence = self._parse_json_int(parsed_json.get("confidence"))
                    if fingerprint_id is None or confidence is None:
                        return None
                    return self._handle_json_match_scan(fingerprint_id, confidence)
                if event == "card":
                    uid = parsed_json.get("uid")
                    card_type = parsed_json.get("card_type")
                    data = parsed_json.get("data")
                    if data is None:
                        data = parsed_json.get("data_hex")
                    if not uid:
                        return None
                    return self._handle_card_scan(str(uid), data, str(card_type) if card_type else None)
                if event == "card_unreadable":
                    uid = parsed_json.get("uid")
                    return self._handle_unknown_card_scan(
                        str(uid) if uid else None,
                        str(parsed_json.get("reason") or "The RFID card could not be read or authenticated."),
                        str(parsed_json.get("card_type")) if parsed_json.get("card_type") else None,
                    )
                if event == "unknown":
                    self.current_id = None
                    return self._handle_unknown_scan()
                if event == "low_confidence":
                    self.current_id = None
                    return None
            return None

        if line.startswith("ID:"):
            self.current_id = self._parse_int_value(line, "ID:")
            return None

        if line == "UNKNOWN":
            return self._handle_unknown_scan()

        if line.startswith("LOW_CONFIDENCE:"):
            self.current_id = None
            return None

        if line.startswith("CONFIDENCE:") and self.current_id is not None:
            confidence = self._parse_int_value(line, "CONFIDENCE:")
            if confidence is None:
                self.current_id = None
                return None
            return self._handle_confidence_scan(confidence)

        return None

    def reset(self) -> None:
        """Clear internal scan state and cooldown history."""
        self.current_id = None
        self.last_scan = {}

    def lookup_student(self, fingerprint_id: int) -> Optional[StudentRow]:
        return self._student_lookup(fingerprint_id)

    def lookup_card_student(self, uid: str) -> Optional[StudentRow]:
        try:
            normalized_uid = str(uid or "").strip().upper()
            for candidate in self.all_students():
                candidate_uid = str(candidate.get("card_uid") or "").strip().upper()
                if candidate_uid and candidate_uid == normalized_uid:
                    return candidate
        except sqlite3.OperationalError:
            pass
        return self._card_lookup(uid)

    def all_students(self) -> List[StudentRow]:
        return self._all_students()

    def _handle_unknown_scan(self) -> ScanResult:
        now = datetime.now()
        fingerprint_id = 0

        if self._is_in_cooldown(fingerprint_id, now):
            log.info(
                "Unknown scan skipped due to cooldown",
                fingerprint_id=fingerprint_id,
                status="UNKNOWN",
                reason=self._cooldown_reason(fingerprint_id, now),
            )
            return ScanOutcome(
                fingerprint_id=fingerprint_id,
                confidence=0,
                status="UNKNOWN",
                timestamp=now,
                logged=False,
                reason=self._cooldown_reason(fingerprint_id, now),
            ).to_dict()

        try:
            self._log_and_record(fingerprint_id, 0, "UNKNOWN", now)
            return ScanOutcome(
                fingerprint_id=fingerprint_id,
                confidence=0,
                status="UNKNOWN",
                timestamp=now,
                logged=True,
                reason=None,
            ).to_dict()
        except Exception as exc:
            log.error(f"Failed to log unknown-fingerprint scan: {exc}")
            return ScanOutcome(
                fingerprint_id=fingerprint_id,
                confidence=0,
                status="UNKNOWN",
                timestamp=now,
                logged=False,
                reason="Could not record unknown scan (see application log).",
            ).to_dict()

    def _handle_unknown_card_scan(
        self,
        uid: Optional[str],
        reason: str = "Card is unlinked or its encrypted payload is invalid.",
        card_type: Optional[str] = None,
    ) -> ScanResult:
        now = datetime.now()
        fingerprint_id = 0
        if self._is_in_cooldown(fingerprint_id, now):
            return ScanOutcome(
                fingerprint_id=fingerprint_id,
                confidence=0,
                status="UNKNOWN",
                timestamp=now,
                logged=False,
                reason=self._cooldown_reason(fingerprint_id, now),
                method="card",
                uid=uid,
                card_type=card_type,
            ).to_dict()

        try:
            self._log_and_record(fingerprint_id, 0, "UNKNOWN", now)
            return ScanOutcome(
                fingerprint_id=fingerprint_id,
                confidence=0,
                status="UNKNOWN",
                timestamp=now,
                logged=True,
                reason=reason,
                method="card",
                uid=uid,
                card_type=card_type,
            ).to_dict()
        except Exception as exc:
            log.error(f"Failed to log unknown-card scan: {exc}")
            return ScanOutcome(
                fingerprint_id=fingerprint_id,
                confidence=0,
                status="UNKNOWN",
                timestamp=now,
                logged=False,
                reason="Could not record unknown card scan.",
                method="card",
                uid=uid,
                card_type=card_type,
            ).to_dict()

    def _handle_card_scan(self, uid: str, data: Optional[str], card_type: Optional[str] = None) -> Optional[ScanResult]:
        now = datetime.now()
        normalized_uid = normalize_card_uid(uid)
        if not normalized_uid:
            return self._handle_unknown_card_scan(uid, "Card UID is invalid.", card_type)
        if not data:
            return self._handle_unknown_card_scan(uid, "Card does not contain an encrypted DSIS payload.", card_type)
        decoded = decrypt_student_card_payload(str(data), normalized_uid)
        if decoded is None:
            return self._handle_unknown_card_scan(
                uid,
                "Card payload is invalid, tampered, or encrypted for a different UID.",
                card_type,
            )
        fingerprint_id, student_no = decoded
        student = self.lookup_student(fingerprint_id)
        if (
            student is None
            or str(student.get("student_no") or "").strip() != student_no
            or normalize_card_uid(student.get("card_uid")) != normalized_uid
        ):
            return self._handle_unknown_card_scan(
                uid,
                "Encrypted card identity does not match a student linked to this UID.",
                card_type,
            )

        fingerprint_id = int(student["fingerprint_id"])
        if self._is_in_cooldown(fingerprint_id, now):
            log.info(
                "Card scan skipped due to cooldown",
                fingerprint_id=fingerprint_id,
                uid=uid,
                reason=self._cooldown_reason(fingerprint_id, now),
            )
            return ScanOutcome(
                fingerprint_id=fingerprint_id,
                confidence=100,
                status="GOOD MATCH",
                timestamp=now,
                logged=False,
                reason=self._cooldown_reason(fingerprint_id, now),
                method="card",
                uid=uid,
                data=data,
                card_type=card_type,
            ).to_dict()

        try:
            self._log_and_record(fingerprint_id, 100, "GOOD MATCH", now)
            return ScanOutcome(
                fingerprint_id=fingerprint_id,
                confidence=100,
                status="GOOD MATCH",
                timestamp=now,
                logged=True,
                reason=None,
                method="card",
                uid=uid,
                data=data,
                card_type=card_type,
            ).to_dict()
        except Exception as exc:
            log.error(f"Failed to log card attendance for {uid}: {exc}")
            return None

    def _handle_confidence_scan(self, confidence: int) -> Optional[ScanResult]:
        fingerprint_id = self.current_id
        self.current_id = None
        now = datetime.now()

        if fingerprint_id is None:
            return None

        if self._is_in_cooldown(fingerprint_id, now):
            log.info(
                "Scan skipped due to cooldown",
                fingerprint_id=fingerprint_id,
                confidence=confidence,
                reason=self._cooldown_reason(fingerprint_id, now),
            )
            return ScanOutcome(
                fingerprint_id=fingerprint_id,
                confidence=confidence,
                status=None,
                timestamp=now,
                logged=False,
                reason=self._cooldown_reason(fingerprint_id, now),
            ).to_dict()

        status = "GOOD MATCH" if confidence >= self.min_confidence else "WEAK MATCH"

        try:
            self._log_and_record(fingerprint_id, confidence, status, now)
            return ScanOutcome(
                fingerprint_id=fingerprint_id,
                confidence=confidence,
                status=status,
                timestamp=now,
                logged=True,
                reason=None,
            ).to_dict()
        except Exception as exc:
            log.error(f"Failed to log attendance for ID {fingerprint_id}: {exc}")
            return None

    def _handle_json_match_scan(self, fingerprint_id: int, confidence: int) -> Optional[ScanResult]:
        now = datetime.now()

        if self._is_in_cooldown(fingerprint_id, now):
            log.info(
                "Scan skipped due to cooldown",
                fingerprint_id=fingerprint_id,
                confidence=confidence,
                reason=self._cooldown_reason(fingerprint_id, now),
            )
            return ScanOutcome(
                fingerprint_id=fingerprint_id,
                confidence=confidence,
                status=None,
                timestamp=now,
                logged=False,
                reason=self._cooldown_reason(fingerprint_id, now),
            ).to_dict()

        status = "GOOD MATCH" if confidence >= self.min_confidence else "WEAK MATCH"

        try:
            self._log_and_record(fingerprint_id, confidence, status, now)
            return ScanOutcome(
                fingerprint_id=fingerprint_id,
                confidence=confidence,
                status=status,
                timestamp=now,
                logged=True,
                reason=None,
            ).to_dict()
        except Exception as exc:
            log.error(f"Failed to log attendance for ID {fingerprint_id}: {exc}")
            return None

    def _parse_json_int(self, value: Any) -> Optional[int]:
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value.strip())
            except ValueError:
                return None
        return None

    def _parse_int_value(self, line: str, prefix: str) -> Optional[int]:
        try:
            return int(line.split(prefix, 1)[1])
        except (ValueError, IndexError):
            return None

    def _is_in_cooldown(self, fingerprint_id: int, now: datetime) -> bool:
        last_seen = self.last_scan.get(fingerprint_id)
        if last_seen is None:
            return False
        return (now - last_seen).total_seconds() < self.cooldown_seconds

    def _cooldown_reason(self, fingerprint_id: int, now: datetime) -> str:
        last_seen = self.last_scan.get(fingerprint_id)
        elapsed = (now - last_seen).total_seconds() if last_seen else 0.0
        return f"Cooldown ({elapsed:.1f}s / {self.cooldown_seconds}s)"

    def _log_and_record(self, fingerprint_id: int, confidence: int, status: str, now: datetime) -> None:
        self._log_attendance(fingerprint_id, confidence, status, now)
        log.info(
            "Attendance scan recorded",
            fingerprint_id=fingerprint_id,
            confidence=confidence,
            status=status,
            timestamp=now.isoformat(),
        )
        self.last_scan[fingerprint_id] = now
