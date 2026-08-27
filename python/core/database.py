"""Persistence layer for students, attendance events, reports, and backup helpers.

This module centralizes SQLite access for the Digital Student Identification System (DSIS) and
keeps the rest of the application focused on workflow logic instead of raw SQL.
"""

import os
import re
import shutil
import sqlite3
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, TypedDict

from config import DB_PATH, get_config
from core.logger import log

CONFIG = get_config()
DB_PATH = str(CONFIG.db_path)

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    CHARTS_AVAILABLE = True
except ImportError:
    plt = None  # type: ignore[assignment]
    CHARTS_AVAILABLE = False


RowDict = Dict[str, Any]


class ValidationState(str, Enum):
    VALID = "valid"
    MISSING = "missing"
    INVALID_FORMAT = "invalid_format"
    UNSUPPORTED_CHARACTER = "unsupported_character"
    TOO_LONG = "too_long"
    INVALID_RANGE = "invalid_range"


@dataclass
class FieldValidationResult:
    field: str
    state: ValidationState
    message: str
    valid: bool = False


STUDENT_NO_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")
STUDENT_NAME_PATTERN = re.compile(r"^[\w ,.'-]+$", re.UNICODE)
GRADE_SECTION_PATTERN = re.compile(r"^[A-Za-z0-9 /-]+$")

_ALLOWED_NAME_PUNCTUATION = set(" ,.'-")


def _is_valid_name_character(ch: str) -> bool:
    """Allow Unicode letters while still rejecting control characters and unsafe symbols.

    This keeps the validation locale-independent: Python sees Unicode codepoints
    directly, so names like José, Müller, Sørensen, Łukasz, and Chloë remain
    intact without needing any OS locale changes.
    """
    if ch in _ALLOWED_NAME_PUNCTUATION:
        return True
    if ch.isspace():
        return True
    if unicodedata.category(ch).startswith("M"):
        return True
    if ch.isalpha():
        return True
    return False


def _is_valid_student_name(value: str) -> bool:
    if not value:
        return False
    if any(ch in {"\x00", "\n", "\r", "\t"} for ch in value):
        return False
    if not any(ch.isalpha() for ch in value):
        return False
    return all(_is_valid_name_character(ch) for ch in value)


def _collect_unsupported_characters(value: str, allowed_chars: Iterable[str]) -> List[str]:
    allowed = set(allowed_chars)
    chars: List[str] = []
    for ch in value:
        if ch in allowed:
            continue
        if ch not in chars:
            chars.append(ch)
    return chars


def _collect_unsupported_name_characters(value: str) -> List[str]:
    chars: List[str] = []
    for ch in value:
        if _is_valid_name_character(ch):
            continue
        if ch not in chars:
            chars.append(ch)
    return chars


def _format_unsupported_characters(chars: List[str]) -> str:
    if not chars:
        return ""
    if len(chars) == 1:
        return chars[0]
    return ", ".join(chars)


class ManagedConnection:
    """Wrap a sqlite3 connection so it always closes when leaving a context."""

    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection

    def __enter__(self) -> sqlite3.Connection:
        return self._connection

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        try:
            if exc_type is None:
                self._connection.commit()
            else:
                self._connection.rollback()
        finally:
            self._connection.close()

    def close(self) -> None:
        self._connection.close()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._connection, name)


class AttendanceRow(TypedDict, total=False):
    id: int
    fingerprint_id: int
    student_no: str
    student_name: str
    grade: str
    section: str
    date: str
    time: str
    confidence: int
    status: str
    event_type: str


class StudentRow(TypedDict, total=False):
    fingerprint_id: int
    student_no: str
    student_name: str
    grade: str
    section: str
    enrollment_date: str
    updated_date: str


ATTENDANCE_JOIN_QUERY = """
    SELECT
        a.id,
        a.fingerprint_id,
        COALESCE(s.student_no, 'N/A') AS student_no,
        CASE WHEN a.fingerprint_id = 0 THEN 'Unregistered' ELSE COALESCE(s.student_name, 'Unknown ID:' || a.fingerprint_id) END AS student_name,
        COALESCE(s.grade, 'N/A') AS grade,
        COALESCE(s.section, 'N/A') AS section,
        a.date,
        a.time,
        a.confidence,
        a.status,
        a.event_type
    FROM attendance a
    LEFT JOIN students s ON a.fingerprint_id = s.fingerprint_id
"""


def get_connection() -> ManagedConnection:
    """Open and configure a database connection."""
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    # Increase timeout to reduce chance of 'database is locked' errors
    connection = sqlite3.connect(DB_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return ManagedConnection(connection)


def _row_dicts(rows: Iterable[sqlite3.Row]) -> List[RowDict]:
    return [dict(row) for row in rows]


def init_database() -> None:
    """Create database tables and indexes if they do not already exist."""
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                fingerprint_id  INTEGER PRIMARY KEY,
                student_no      TEXT    NOT NULL UNIQUE,
                student_name    TEXT    NOT NULL,
                grade           TEXT    NOT NULL,
                section         TEXT    NOT NULL,
                enrollment_date TEXT    NOT NULL,
                updated_date    TEXT    NOT NULL
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_student_no ON students(student_no)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_grade_section ON students(grade, section)")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS attendance (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                fingerprint_id  INTEGER NOT NULL,
                date            TEXT    NOT NULL,
                time            TEXT    NOT NULL,
                confidence      INTEGER NOT NULL,
                status          TEXT    NOT NULL,
                timestamp       TEXT    NOT NULL,
                event_type      TEXT,
                FOREIGN KEY (fingerprint_id) REFERENCES students(fingerprint_id)
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_attendance_fingerprint_id ON attendance(fingerprint_id)"
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_timestamp ON attendance(timestamp)")

        _migrate_attendance_event_type(cursor)

        conn.execute("DELETE FROM students WHERE fingerprint_id <= 0")
        conn.commit()
    finally:
        conn.close()

    log.success(f"Database ready at {os.path.abspath(DB_PATH)}")


def _migrate_attendance_event_type(cursor: sqlite3.Cursor) -> None:
    """Add and backfill the `event_type` column for databases created before it existed.

    Older rows have no event_type, so Time-In/Time-Out was only ever inferred
    later (in get_daily_attendance_summary) from scan order within a day.
    That's fragile - it breaks if scans are ever reordered or two students
    scan in the same second. This tags each row explicitly, once, so future
    reads don't have to guess:
      - the first scan of a (fingerprint_id, date) is 'time_in'
      - every later scan that same day is 'time_out'
    """
    cursor.execute("PRAGMA table_info(attendance)")
    columns = {row[1] for row in cursor.fetchall()}
    if "event_type" not in columns:
        cursor.execute("ALTER TABLE attendance ADD COLUMN event_type TEXT")

    cursor.execute(
        "SELECT id, fingerprint_id, date FROM attendance "
        "WHERE event_type IS NULL OR event_type = '' "
        "ORDER BY fingerprint_id, date, time ASC, id ASC"
    )
    rows_to_backfill = cursor.fetchall()
    if not rows_to_backfill:
        return

    seen_today: set = set()
    for row_id, fingerprint_id, date_str in rows_to_backfill:
        key = (fingerprint_id, date_str)
        event_type = "time_in" if key not in seen_today else "time_out"
        seen_today.add(key)
        cursor.execute(
            "UPDATE attendance SET event_type = ? WHERE id = ?",
            (event_type, row_id),
        )


# -----------------------------------------------------------------------------
# Student operations
# -----------------------------------------------------------------------------


def validate_student_input(
    fingerprint_id: int,
    student_no: str,
    student_name: str,
    grade: str,
    section: str,
) -> Tuple[bool, str]:
    """Validate student input fields.
    
    Args:
        fingerprint_id: AS608 template ID (1-127)
        student_no: Student ID number
        student_name: Student's full name
        grade: Grade/class level
        section: Section/class section
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Fingerprint ID validation (AS608 sensor uses 1-127)
    if not isinstance(fingerprint_id, int) or fingerprint_id < 1 or fingerprint_id > 127:
        return False, "Fingerprint ID must be between 1 and 127"
    
    # Student number validation
    if not student_no or not isinstance(student_no, str):
        return False, "Student number is required"
    
    student_no_stripped = student_no.strip()
    if len(student_no_stripped) < 1 or len(student_no_stripped) > 50:
        return False, "Student number must be 1-50 characters"
    
    if not STUDENT_NO_PATTERN.fullmatch(student_no_stripped):
        return False, "Student number contains invalid characters. Use letters, numbers, dots, hyphens, or underscores."
    
    # Student name validation
    if not student_name or not isinstance(student_name, str):
        return False, "Student name is required"
    
    student_name_stripped = student_name.strip()
    if len(student_name_stripped) < 1 or len(student_name_stripped) > 100:
        return False, "Student name must be 1-100 characters"
    
    if not _is_valid_student_name(student_name_stripped):
        return False, "Student name contains invalid characters"
    
    # Grade validation
    if not grade or not isinstance(grade, str):
        return False, "Grade is required"
    
    grade_stripped = grade.strip()
    if len(grade_stripped) < 1 or len(grade_stripped) > 50:
        return False, "Grade must be 1-50 characters"
    
    if not GRADE_SECTION_PATTERN.fullmatch(grade_stripped):
        return False, "Grade contains invalid characters"
    
    # Section validation
    if not section or not isinstance(section, str):
        return False, "Section is required"
    
    section_stripped = section.strip()
    if len(section_stripped) < 1 or len(section_stripped) > 50:
        return False, "Section must be 1-50 characters"
    
    if not GRADE_SECTION_PATTERN.fullmatch(section_stripped):
        return False, "Section contains invalid characters"
    
    return True, ""


def get_student_field_feedback(
    fingerprint_id: int,
    student_no: str,
    student_name: str,
    grade: str,
    section: str,
) -> Dict[str, FieldValidationResult]:
    """Return human-friendly validation feedback for each student field.

    This reuses the centralized validation rules in validate_student_input() while
    exposing per-field, user-friendly state and messaging for live UI feedback.
    """
    feedback: Dict[str, FieldValidationResult] = {}

    def add_feedback(field_name: str, state: ValidationState, message: str):
        feedback[field_name] = FieldValidationResult(field_name, state, message, state == ValidationState.VALID)

    def check_name(value: str, field_name: str, max_length: int):
        if value is None:
            value = ""
        value = str(value).strip()
        if value == "":
            add_feedback(field_name, ValidationState.MISSING, "Required field")
            return
        if len(value) > max_length:
            add_feedback(field_name, ValidationState.TOO_LONG, f"Too many characters ({len(value)}/{max_length})")
            return
        if not _is_valid_student_name(value):
            unsupported = _collect_unsupported_name_characters(value)
            if unsupported:
                add_feedback(field_name, ValidationState.UNSUPPORTED_CHARACTER, f"Unsupported character: {_format_unsupported_characters(unsupported)}")
            else:
                add_feedback(field_name, ValidationState.INVALID_FORMAT, "Invalid full name format")
            return
        add_feedback(field_name, ValidationState.VALID, "Valid")

    def check_token(value: str, field_name: str, max_length: int, allowed_chars: str, invalid_message: str, pattern: str):
        if value is None:
            value = ""
        value = str(value).strip()
        if value == "":
            add_feedback(field_name, ValidationState.MISSING, "Required field")
            return
        if len(value) > max_length:
            add_feedback(field_name, ValidationState.TOO_LONG, f"Too many characters ({len(value)}/{max_length})")
            return
        if not re.fullmatch(pattern, value):
            unsupported = _collect_unsupported_characters(value, allowed_chars)
            if unsupported:
                add_feedback(field_name, ValidationState.UNSUPPORTED_CHARACTER, f"Unsupported character: {_format_unsupported_characters(unsupported)}")
            else:
                add_feedback(field_name, ValidationState.INVALID_FORMAT, invalid_message)
            return
        add_feedback(field_name, ValidationState.VALID, "Valid")

    student_no_value = student_no if student_no is not None else ""
    student_name_value = student_name if student_name is not None else ""
    grade_value = grade if grade is not None else ""
    section_value = section if section is not None else ""

    check_token(student_no_value, "student_no", 50, "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-", "Invalid student number format", r"[A-Za-z0-9._-]+")
    check_name(student_name_value, "student_name", 100)
    check_token(grade_value, "grade", 50, "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/- ", "Invalid grade format. Example: 12", r"[A-Za-z0-9 /-]+")
    check_token(section_value, "section", 50, "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/- ", "Section format is invalid. Example: CSS-12-1", r"[A-Za-z0-9 /-]+")

    all_valid, _ = validate_student_input(fingerprint_id, student_no_value, student_name_value, grade_value, section_value)
    if all_valid:
        for field_name, result in feedback.items():
            result.valid = True
            result.state = ValidationState.VALID
            result.message = "Valid"
    return feedback


def add_student(
    fingerprint_id: int,
    student_no: str,
    student_name: str,
    grade: str,
    section: str,
) -> Tuple[bool, str]:
    # Validate input before attempting to insert
    is_valid, error_msg = validate_student_input(
        fingerprint_id, student_no, student_name, grade, section
    )
    if not is_valid:
        return False, error_msg

    now = datetime.now().isoformat()
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO students
            (fingerprint_id, student_no, student_name, grade, section, enrollment_date, updated_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (fingerprint_id, student_no, student_name, grade, section, now, now),
        )
        conn.commit()
        return True, "OK"
    except sqlite3.IntegrityError as exc:
        message = str(exc)
        if "fingerprint_id" in message:
            return False, f"Fingerprint ID {fingerprint_id} already assigned to a student."
        if "student_no" in message:
            return False, f"Student number {student_no} already exists."
        return False, message
    finally:
        conn.close()


def update_student(
    fingerprint_id: int,
    student_no: str,
    student_name: str,
    grade: str,
    section: str,
) -> Tuple[bool, str]:
    # Validate input before attempting to update
    is_valid, error_msg = validate_student_input(
        fingerprint_id, student_no, student_name, grade, section
    )
    if not is_valid:
        return False, error_msg

    now = datetime.now().isoformat()
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE students
            SET student_no = ?, student_name = ?, grade = ?, section = ?, updated_date = ?
            WHERE fingerprint_id = ?
            """,
            (student_no, student_name, grade, section, now, fingerprint_id),
        )
        conn.commit()
        return True, "OK"
    except sqlite3.IntegrityError as exc:
        return False, str(exc)
    finally:
        conn.close()


def delete_student(fingerprint_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM students WHERE fingerprint_id = ?", (fingerprint_id,))
        conn.commit()
    finally:
        conn.close()


def clear_all_students() -> int:
    students = get_all_students()
    conn = get_connection()
    try:
        conn.execute("DELETE FROM attendance")
        conn.execute("DELETE FROM students")
        conn.commit()
        return len(students)
    finally:
        conn.close()


def get_student(fingerprint_id: int) -> Optional[StudentRow]:
    if fingerprint_id <= 0:
        return None

    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM students WHERE fingerprint_id = ?",
            (fingerprint_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_all_students() -> List[StudentRow]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM students ORDER BY fingerprint_id").fetchall()
        return _row_dicts(rows)
    finally:
        conn.close()


def get_student_count() -> int:
    conn = get_connection()
    try:
        return conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    finally:
        conn.close()


def register_student(
    fingerprint_id: int,
    student_no: str,
    student_name: str,
    grade: str,
    section: str,
) -> Tuple[bool, str]:
    existing = get_student(fingerprint_id)
    if existing:
        return update_student(fingerprint_id, student_no, student_name, grade, section)
    return add_student(fingerprint_id, student_no, student_name, grade, section)


def import_students_from_list(students: List[Dict[str, Any]]) -> Dict[str, Any]:
    results = {"success": 0, "failed": 0, "errors": []}
    for student in students:
        ok, msg = register_student(
            student["fingerprint_id"],
            student["student_no"],
            student["student_name"],
            student["grade"],
            student["section"],
        )
        if ok:
            results["success"] += 1
        else:
            results["failed"] += 1
            results["errors"].append(f"ID {student['fingerprint_id']}: {msg}")
    return results


# -----------------------------------------------------------------------------
# Attendance operations
# -----------------------------------------------------------------------------


def log_attendance(
    fingerprint_id: int,
    confidence: int,
    status: str,
    now: Optional[datetime] = None,
) -> None:
    now = now or datetime.now()
    timestamp = now.isoformat()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    with get_connection() as conn:
        # Tag Time-In/Time-Out at the moment of the scan instead of leaving
        # it to be inferred later from row order: the first scan for this
        # fingerprint today is 'time_in', any later scan that day is
        # 'time_out'.
        already_scanned_today = conn.execute(
            "SELECT 1 FROM attendance WHERE fingerprint_id = ? AND date = ? LIMIT 1",
            (fingerprint_id, date_str),
        ).fetchone()
        event_type = "time_out" if already_scanned_today else "time_in"

        conn.execute(
            """
            INSERT INTO attendance (fingerprint_id, date, time, confidence, status, timestamp, event_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (fingerprint_id, date_str, time_str, confidence, status, timestamp, event_type),
        )
        conn.commit()


def get_attendance_today() -> List[AttendanceRow]:
    """Return today's attendance rows (kept for backward compatibility).

    NOTE: this silently falls back to the most recent 25 records from *any*
    date when today has none - callers that need to know whether that
    happened (to label the UI accordingly) should use
    get_today_attendance_info() instead.
    """
    return get_today_attendance_info()["rows"]


def get_today_attendance_info() -> Dict[str, Any]:
    """Return today's attendance rows plus whether a fallback was used.

    Returns:
        {"rows": [...], "is_fallback": bool}
        is_fallback is True when there were no records for today's date and
        the result is instead the most recent 25 records overall - useful so
        the UI can say "showing recent activity" instead of implying these
        rows are from today.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    query = f"{ATTENDANCE_JOIN_QUERY} WHERE a.date = ? ORDER BY a.timestamp DESC, a.id DESC"
    conn = get_connection()
    try:
        rows = conn.execute(query, (today,)).fetchall()
        if rows:
            return {"rows": _row_dicts(rows), "is_fallback": False}

        # Some databases contain historical or imported entries. If the live
        # date has no records, fall back to the newest attendance records so the
        # UI and tests still display the most recent activity without breaking
        # on empty "today" buckets.
        fallback_query = f"{ATTENDANCE_JOIN_QUERY} ORDER BY a.timestamp DESC, a.id DESC LIMIT 25"
        rows = conn.execute(fallback_query).fetchall()
        return {"rows": _row_dicts(rows), "is_fallback": bool(rows)}
    finally:
        conn.close()


def get_attendance_all() -> List[AttendanceRow]:
    query = f"{ATTENDANCE_JOIN_QUERY} ORDER BY a.timestamp DESC"
    conn = get_connection()
    try:
        rows = conn.execute(query).fetchall()
        return _row_dicts(rows)
    finally:
        conn.close()


def get_attendance_paginated(limit: int = 100, offset: int = 0) -> List[AttendanceRow]:
    query = f"{ATTENDANCE_JOIN_QUERY} ORDER BY a.timestamp DESC, a.id DESC LIMIT ? OFFSET ?"
    conn = get_connection()
    try:
        rows = conn.execute(query, (limit, offset)).fetchall()
        return _row_dicts(rows)
    finally:
        conn.close()


def get_attendance_count_today() -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    with get_connection() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM attendance WHERE date = ?",
            (today,),
        ).fetchone()[0]


def get_daily_attendance_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[RowDict]:
    filters: List[str] = []
    params: List[Any] = []

    if start_date:
        filters.append("a.date >= ?")
        params.append(start_date)
    if end_date:
        filters.append("a.date <= ?")
        params.append(end_date)

    where_clause = " AND ".join(filters)
    query = f"{ATTENDANCE_JOIN_QUERY}"
    if where_clause:
        query += f" WHERE {where_clause}"
    query += " ORDER BY a.date ASC, a.time ASC, a.timestamp ASC"

    with get_connection() as conn:
        rows = conn.execute(query, tuple(params)).fetchall()

    grouped: Dict[Tuple[str, str], RowDict] = {}
    for row in rows:
        row_dict = dict(row)
        key = (row_dict["student_name"], row_dict["date"])
        entry = grouped.setdefault(
            key,
            {
                "student_name": row_dict["student_name"],
                "student_no": row_dict["student_no"],
                "grade": row_dict["grade"],
                "section": row_dict["section"],
                "date": row_dict["date"],
                "time_in": row_dict["time"],
                "time_out": row_dict["time"],
                "status": row_dict["status"],
            },
        )

        # Prefer the event_type tagged at scan time. Rows written before the
        # event_type migration (or ones that somehow slipped through without
        # one) fall back to the old "last scan seen = time_out" behavior so
        # nothing breaks for older data.
        event_type = row_dict.get("event_type")
        if event_type == "time_in":
            entry["time_in"] = row_dict["time"]
        elif event_type == "time_out":
            entry["time_out"] = row_dict["time"]
        else:
            entry["time_out"] = row_dict["time"]

        if str(row_dict["status"]).lower() in {"present", "logged", "ok"}:
            entry["status"] = row_dict["status"]

    return list(grouped.values())


def get_attendance_by_date(date_str: str) -> List[AttendanceRow]:
    query = f"{ATTENDANCE_JOIN_QUERY} WHERE a.date = ? ORDER BY a.time"
    conn = get_connection()
    try:
        rows = conn.execute(query, (date_str,)).fetchall()
        return _row_dicts(rows)
    finally:
        conn.close()


def clear_all_attendance() -> int:
    conn = get_connection()
    try:
        count = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
        conn.execute("DELETE FROM attendance")
        conn.commit()
        return count
    finally:
        conn.close()


def clear_all_data() -> Tuple[int, int]:
    conn = get_connection()
    try:
        student_count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        attendance_count = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
        conn.execute("DELETE FROM attendance")
        conn.execute("DELETE FROM students")
        conn.commit()
        return student_count, attendance_count
    finally:
        conn.close()


def get_attendance_by_student(fingerprint_id: int) -> List[AttendanceRow]:
    query = f"{ATTENDANCE_JOIN_QUERY} WHERE a.fingerprint_id = ? ORDER BY a.date DESC, a.time DESC"
    conn = get_connection()
    try:
        rows = conn.execute(query, (fingerprint_id,)).fetchall()
        return _row_dicts(rows)
    finally:
        conn.close()


def get_students_by_grade_section(grade: str, section: str) -> List[StudentRow]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM students WHERE grade = ? AND section = ? ORDER BY student_name",
            (grade, section),
        ).fetchall()
        return _row_dicts(rows)
    finally:
        conn.close()


def count_attendance_by_date(date_str: str) -> int:
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT COUNT(*) FROM attendance WHERE date = ?",
            (date_str,),
        ).fetchone()[0]
    finally:
        conn.close()


def get_attendance_statistics() -> RowDict:
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
        unique_students = conn.execute(
            "SELECT COUNT(DISTINCT fingerprint_id) FROM attendance"
        ).fetchone()[0]

        status_counts = {
            row["status"]: row["count"]
            for row in conn.execute(
                "SELECT status, COUNT(*) as count FROM attendance GROUP BY status"
            ).fetchall()
        }

        avg_confidence = conn.execute(
            "SELECT AVG(confidence) FROM attendance"
        ).fetchone()[0] or 0
        avg_confidence = round(avg_confidence, 2)

        date_info = conn.execute(
            "SELECT MIN(date) as earliest, MAX(date) as latest FROM attendance"
        ).fetchone()

        return {
            "total_scans": total,
            "unique_students": unique_students,
            "status_breakdown": status_counts,
            "average_confidence": avg_confidence,
            "earliest_date": date_info["earliest"],
            "latest_date": date_info["latest"],
        }
    finally:
        conn.close()


def get_students_statistics() -> RowDict:
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]

        grade_counts = {
            row["grade"]: row["count"]
            for row in conn.execute(
                "SELECT grade, COUNT(*) as count FROM students GROUP BY grade ORDER BY grade"
            ).fetchall()
        }

        section_counts = {
            row["section"]: row["count"]
            for row in conn.execute(
                "SELECT section, COUNT(*) as count FROM students GROUP BY section ORDER BY section"
            ).fetchall()
        }

        return {
            "total_students": total,
            "by_grade": grade_counts,
            "by_section": section_counts,
        }
    finally:
        conn.close()


def export_attendance_range(start_date: str, end_date: str) -> List[AttendanceRow]:
    query = f"{ATTENDANCE_JOIN_QUERY} WHERE a.date >= ? AND a.date <= ? ORDER BY a.date ASC, a.time ASC"
    conn = get_connection()
    try:
        rows = conn.execute(query, (start_date, end_date)).fetchall()
        return _row_dicts(rows)
    finally:
        conn.close()


def generate_statistics_report() -> str:
    conn = get_connection()
    try:
        total_students = conn.execute("SELECT COUNT(*) as count FROM students").fetchone()["count"]
        total_attendance = conn.execute("SELECT COUNT(*) as count FROM attendance").fetchone()["count"]

        attendance_by_date = conn.execute(
            "SELECT date, COUNT(*) as count FROM attendance GROUP BY date ORDER BY date DESC LIMIT 30"
        ).fetchall()

        top_students = conn.execute(
            """
            SELECT COALESCE(s.student_name, 'Unknown') as name,
                   COUNT(a.id) as count
            FROM attendance a
            LEFT JOIN students s ON a.fingerprint_id = s.fingerprint_id
            GROUP BY a.fingerprint_id
            ORDER BY count DESC
            LIMIT 10
            """
        ).fetchall()

        grade_stats = conn.execute(
            "SELECT grade, COUNT(*) as count FROM students GROUP BY grade"
        ).fetchall()

        enrolled_students = conn.execute(
            "SELECT student_name, student_no, grade, section FROM students ORDER BY student_name COLLATE NOCASE, fingerprint_id ASC"
        ).fetchall()

        report_lines = [
            "=" * 70,
            "ATTENDANCE STATISTICS REPORT",
            "=" * 70,
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "─" * 70,
            "KEY METRICS",
            "─" * 70,
            f"Total Students Enrolled: {total_students}",
            f"Total Attendance Records: {total_attendance}",
            f"Average per Student: {total_attendance / max(total_students, 1):.1f} records",
            "",
            "─" * 70,
            "TOP 10 STUDENTS (By Attendance Count)",
            "─" * 70,
        ]

        if top_students:
            for i, row in enumerate(top_students, 1):
                report_lines.append(f"{i:2d}. {row['name']:<30s} {row['count']:4d} scans")
        else:
            report_lines.append("No attendance records yet.")

        report_lines.extend([
            "",
            "─" * 70,
            "STUDENTS BY GRADE",
            "─" * 70,
        ])

        if grade_stats:
            for row in grade_stats:
                grade_label = row["grade"] or "Unspecified"
                report_lines.append(f"{grade_label:<20s} {row['count']:4d} students")
        else:
            report_lines.append("No students registered.")

        report_lines.extend([
            "",
            "─" * 70,
            "ENROLLED STUDENTS",
            "─" * 70,
        ])

        if enrolled_students:
            for row in enrolled_students:
                name = row["student_name"] or "Unknown Student"
                student_no = row["student_no"] or "N/A"
                grade = row["grade"] or "N/A"
                section = row["section"] or "N/A"
                report_lines.append(f"{name:<30s} | {student_no:<12s} | Grade {grade} | {section}")
        else:
            report_lines.append("No students registered.")

        report_lines.extend([
            "",
            "─" * 70,
            "RECENT ATTENDANCE (Last 30 Days)",
            "─" * 70,
        ])

        if attendance_by_date:
            for row in attendance_by_date:
                report_lines.append(f"{row['date']}  {row['count']:4d} scans")
        else:
            report_lines.append("No attendance records yet.")

        report_lines.extend(["", "=" * 70])
        return "\n".join(report_lines)
    except Exception as exc:
        log.error(f"Report generation failed: {exc}")
        return f"Error generating report: {exc}"
    finally:
        conn.close()


def _save_chart(fig: Any, filename: str) -> Optional[str]:
    chart_dir = Path(DB_PATH).parent / "charts"
    chart_dir.mkdir(parents=True, exist_ok=True)
    chart_path = chart_dir / filename
    fig.savefig(str(chart_path), dpi=80, bbox_inches='tight')
    fig.clf()
    return str(chart_path)


def generate_attendance_chart() -> Optional[str]:
    if not CHARTS_AVAILABLE or plt is None:
        return None

    try:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT date, COUNT(*) as count FROM attendance GROUP BY date ORDER BY date DESC LIMIT 30"
            ).fetchall()

        if not rows:
            return None

        dates = [row["date"] for row in reversed(rows)]
        counts = [row["count"] for row in reversed(rows)]

        fig, ax = plt.subplots(figsize=(10, 4), dpi=80)
        ax.plot(range(len(dates)), counts, marker='o', linewidth=2, markersize=6, color='#3b82f6')
        ax.fill_between(range(len(dates)), counts, alpha=0.3, color='#3b82f6')
        ax.set_xlabel('Date', fontsize=10)
        ax.set_ylabel('Attendance Count', fontsize=10)
        ax.set_title('Attendance Timeline (Last 30 Days)', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)

        step = max(1, len(dates) // 10)
        ax.set_xticks(range(0, len(dates), step))
        ax.set_xticklabels(dates[::step], rotation=45, ha='right', fontsize=8)

        plt.tight_layout()
        return _save_chart(fig, 'attendance_timeline.png')
    except Exception as exc:
        log.error(f"Attendance chart generation failed: {exc}")
        return None


def generate_section_chart() -> Optional[str]:
    if not CHARTS_AVAILABLE or plt is None:
        return None

    try:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT section, COUNT(*) as count FROM students WHERE section IS NOT NULL AND section != '' GROUP BY section ORDER BY count DESC"
            ).fetchall()

        if not rows:
            return None

        sections = [row["section"] for row in rows]
        counts = [row["count"] for row in rows]

        fig, ax = plt.subplots(figsize=(10, 4), dpi=80)
        colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
        ax.bar(sections, counts, color=colors[: len(sections)], edgecolor='black', linewidth=1.2)
        ax.set_xlabel('Section', fontsize=10)
        ax.set_ylabel('Number of Students', fontsize=10)
        ax.set_title('Students by Section', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')

        for i, cnt in enumerate(counts):
            ax.text(i, cnt + 0.1, str(cnt), ha='center', va='bottom', fontweight='bold')

        plt.tight_layout()
        return _save_chart(fig, 'section_chart.png')
    except Exception as exc:
        log.error(f"Section chart generation failed: {exc}")
        return None


def generate_grade_chart() -> Optional[str]:
    if not CHARTS_AVAILABLE or plt is None:
        return None

    try:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT COALESCE(s.grade, 'Unspecified') as grade, COUNT(a.id) as count
                FROM attendance a
                LEFT JOIN students s ON a.fingerprint_id = s.fingerprint_id
                GROUP BY s.grade
                ORDER BY count DESC
                """
            ).fetchall()

        if not rows:
            return None

        grades = [row["grade"] for row in rows]
        counts = [row["count"] for row in rows]

        fig, ax = plt.subplots(figsize=(8, 6), dpi=80)
        colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']
        wedges, texts, autotexts = ax.pie(
            counts,
            labels=grades,
            autopct='%1.1f%%',
            colors=colors[: len(grades)],
            startangle=90,
        )

        for text in texts:
            text.set_fontsize(10)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(9)

        ax.set_title('Attendance by Grade', fontsize=12, fontweight='bold')
        plt.tight_layout()
        return _save_chart(fig, 'grade_chart.png')
    except Exception as exc:
        log.error(f"Grade chart generation failed: {exc}")
        return None


def backup_database() -> Tuple[bool, str, Optional[str]]:
    try:
        backup_dir = Path(DB_PATH).parent / 'backups'
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = backup_dir / f'attendance_{timestamp}.db'

        if Path(DB_PATH).exists():
            shutil.copy2(DB_PATH, backup_path)
            log.success(f"Database backed up to {backup_path}")
            return True, f"Backup created: {backup_path.name}", str(backup_path)
        return False, 'Database file not found', None
    except Exception as exc:
        log.error(f"Database backup failed: {exc}")
        return False, f"Backup failed: {exc}", None


def restore_database(backup_path: str) -> Tuple[bool, str]:
    """Restore database from a backup file.
    
    Args:
        backup_path: Path to the backup file. Must be within the backups directory.
    
    Returns:
        Tuple of (success, message)
    """
    try:
        backup_file = Path(backup_path).resolve()
        backup_dir = (Path(DB_PATH).parent / 'backups').resolve()
        
        # SECURITY: Ensure the backup file is within the backups directory
        # This prevents path traversal attacks
        if not str(backup_file).startswith(str(backup_dir)):
            log.error(f"Restore attempted from outside backups directory: {backup_path}")
            return False, 'Invalid backup file location. Backups must be in the backups directory.'
        
        if not backup_file.exists():
            return False, 'Backup file not found'
        
        # Verify file is a SQLite database before restoring
        if not backup_file.suffix == '.db':
            return False, 'Invalid file type. Only .db backup files are supported.'
        
        shutil.copy2(backup_file, DB_PATH)
        log.success(f"Database restored from {backup_file.name}")
        return True, 'Database restored successfully'
    except Exception as exc:
        log.error(f"Database restore failed: {exc}")
        return False, 'Restore failed. Please try again.'


def list_backups() -> List[RowDict]:
    try:
        backup_dir = Path(DB_PATH).parent / 'backups'
        if not backup_dir.exists():
            return []

        backups: List[RowDict] = []
        for backup_file in sorted(backup_dir.glob('attendance_*.db'), reverse=True):
            stat = backup_file.stat()
            backups.append(
                {
                    'name': backup_file.name,
                    'path': str(backup_file),
                    'size_mb': f"{stat.st_size / (1024 * 1024):.2f} MB",
                    'date': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                }
            )
        return backups
    except Exception as exc:
        log.error(f"Failed to list backups: {exc}")
        return []


def auto_backup_if_needed(min_interval_hours: float = 24.0) -> Optional[str]:
    """Create a backup if enough time has passed since the most recent one.

    Meant to be called on startup and/or on a recurring timer. Never raises -
    any failure (disk full, permissions, corrupt backups folder, etc.) is
    logged and swallowed so it can't interrupt the caller.

    Args:
        min_interval_hours: Minimum hours that must have elapsed since the
            last backup before a new one is created.

    Returns:
        Path to the newly created backup file, or None if no backup was
        due yet, or if backup creation failed.
    """
    try:
        existing = list_backups()
        if existing:
            last_backup_time = datetime.strptime(existing[0]['date'], '%Y-%m-%d %H:%M:%S')
            elapsed_hours = (datetime.now() - last_backup_time).total_seconds() / 3600
            if elapsed_hours < min_interval_hours:
                return None

        success, _message, backup_path = backup_database()
        return backup_path if success else None
    except Exception as exc:
        log.error(f"Auto-backup check failed: {exc}")
        return None