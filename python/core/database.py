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
    card_uid: Optional[str]
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


def export_name_sort_key(value: Any) -> str:
    """Return a stable alphabetical key that ignores accents and case."""
    text = "" if value is None else str(value)
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(char for char in normalized if not unicodedata.combining(char)).casefold()


def get_connection() -> ManagedConnection:
    """Open and configure a database connection."""
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    # Coordinate concurrent readers/writers without changing the schema.
    connection = sqlite3.connect(DB_PATH, timeout=30)
    connection.text_factory = str
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    connection.execute("PRAGMA journal_mode = WAL")
    return ManagedConnection(connection)


def _row_dicts(rows: Iterable[sqlite3.Row]) -> List[RowDict]:
    return [dict(row) for row in rows]


# Explicit column list for `students`, kept in one place so every query
# below stays in sync with the CREATE TABLE statement instead of relying on
# `SELECT *` (which silently reshapes every caller's rows the moment a
# column like email/phone/photo/status gets added later).
STUDENT_COLUMNS = (
    "fingerprint_id",
    "student_no",
    "student_name",
    "grade",
    "section",
    "card_uid",
    "enrollment_date",
    "updated_date",
)
_STUDENT_COLUMNS_SQL = ", ".join(STUDENT_COLUMNS)


def _student_select_sql(conn: sqlite3.Connection) -> str:
    """Return the safe SELECT list for current schema while keeping older DBs working."""
    columns = {row[1] for row in conn.execute("PRAGMA table_info(students)").fetchall()}
    if "card_uid" in columns:
        return _STUDENT_COLUMNS_SQL
    return ", ".join(column for column in STUDENT_COLUMNS if column != "card_uid")


def normalize_card_uid(value: Any) -> Optional[str]:
    """Return a canonical uppercase card UID such as AA:BB:CC:DD."""
    if value is None:
        return None
    text = str(value).strip().upper().replace("-", ":")
    if not text:
        return None
    cleaned = "".join(ch for ch in text if ch in "0123456789ABCDEF:")
    if not cleaned:
        return None
    if ":" in cleaned:
        groups = [chunk for chunk in cleaned.split(":") if chunk]
        if len(groups) == 0:
            return None
        normalized = ":".join(group.zfill(2) for group in groups)
        return normalized if len(normalized.split(":")) >= 2 else None
    if len(cleaned) % 2 != 0:
        cleaned = cleaned[:-1]
    if len(cleaned) < 4:
        return None
    return ":".join(cleaned[i : i + 2] for i in range(0, len(cleaned), 2))


def _student_card_uid_column_exists(cursor: sqlite3.Cursor) -> bool:
    cursor.execute("PRAGMA table_info(students)")
    return any(row[1] == "card_uid" for row in cursor.fetchall())


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
                card_uid        TEXT    UNIQUE,
                enrollment_date TEXT    NOT NULL,
                updated_date    TEXT    NOT NULL
            )
            """
        )
        if not _student_card_uid_column_exists(cursor):
            cursor.execute("ALTER TABLE students ADD COLUMN card_uid TEXT")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_students_card_uid ON students(card_uid) WHERE card_uid IS NOT NULL")
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
        # Match common ordered reads so pagination and date-range summaries
        # have suitable composite indexes rather than relying on single-column
        # indexes plus a separate sort.
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_attendance_timestamp_id ON attendance(timestamp DESC, id DESC)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_attendance_date_time_timestamp ON attendance(date, time, timestamp)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_attendance_student_date_time ON attendance(fingerprint_id, date, time, timestamp)"
        )

        _migrate_attendance_event_type(cursor)

        # ID 0 is the durable Unregistered placeholder used by unknown scans.
        # Only negative IDs are invalid and may be removed during startup.
        conn.execute("DELETE FROM attendance WHERE fingerprint_id < 0")
        conn.execute("DELETE FROM students WHERE fingerprint_id < 0")

        # Seed a permanent placeholder row for fingerprint_id 0, representing
        # "Unregistered/Unknown" scans. The attendance table's FOREIGN KEY on
        # fingerprint_id (enforced via PRAGMA foreign_keys = ON in
        # get_connection()) otherwise rejects every unknown-fingerprint scan
        # outright, since nothing else ever inserts a fingerprint_id=0
        # student. The ATTENDANCE_JOIN_QUERY's `CASE WHEN a.fingerprint_id = 0
        # THEN 'Unregistered'` branch already assumed this row's existence;
        # this is what actually makes that branch reachable.
        now_iso = datetime.now().isoformat()
        conn.execute(
            """
            INSERT INTO students (fingerprint_id, student_no, student_name, grade, section, enrollment_date, updated_date)
            VALUES (0, 'N/A', 'Unregistered', 'N/A', 'N/A', ?, ?)
            ON CONFLICT(fingerprint_id) DO NOTHING
            """,
            (now_iso, now_iso),
        )
        conn.commit()
    finally:
        conn.close()

    log.success(f"Database ready at {os.path.abspath(DB_PATH)}")


def _migrate_attendance_event_type(cursor: sqlite3.Cursor) -> None:
    """Backfill historical event tags for databases created before the column.

    This deterministic migration preserves legacy scan ordering for audit
    purposes only. Historical `time_out` tags on ordinary scan rows are not
    proof of departure; current summaries/exports only recognize an explicit
    row with event_type='time_out' and status='TIME OUT' as a real departure.
    New repeated scans are tagged `scan`.
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
        log.error(f"add_student integrity error: {exc}")
        return False, "Could not save the student. Please check the application logs for more information."
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
        message = str(exc)
        if "student_no" in message:
            return False, f"Student number {student_no} already exists."
        log.error(f"update_student integrity error: {exc}")
        return False, "Could not save the student. Please check the application logs for more information."
    finally:
        conn.close()


def replace_student_fingerprint(
    old_fingerprint_id: int,
    new_fingerprint_id: int,
    student_no: str,
    student_name: str,
    grade: str,
    section: str,
) -> Tuple[bool, str]:
    """Move an existing student record to a newly enrolled fingerprint ID."""
    is_valid, error_msg = validate_student_input(
        new_fingerprint_id, student_no, student_name, grade, section
    )
    if not is_valid:
        return False, error_msg

    conn = get_connection()
    try:
        old_row = conn.execute(
            "SELECT enrollment_date FROM students WHERE fingerprint_id = ?",
            (old_fingerprint_id,),
        ).fetchone()
        if old_row is None:
            return False, f"Student fingerprint ID {old_fingerprint_id} was not found."
        if conn.execute(
            "SELECT 1 FROM students WHERE fingerprint_id = ?",
            (new_fingerprint_id,),
        ).fetchone():
            return False, f"Fingerprint ID {new_fingerprint_id} is already assigned to a student."

        now = datetime.now().isoformat()
        temporary_student_no = f"__reenroll_{old_fingerprint_id}_{int(datetime.now().timestamp() * 1000000)}"
        conn.execute(
            "INSERT INTO students (fingerprint_id, student_no, student_name, grade, section, enrollment_date, updated_date) "
            "SELECT ?, ?, student_name, grade, section, enrollment_date, ? FROM students WHERE fingerprint_id = ?",
            (new_fingerprint_id, temporary_student_no, now, old_fingerprint_id),
        )
        conn.execute(
            "UPDATE attendance SET fingerprint_id = ? WHERE fingerprint_id = ?",
            (new_fingerprint_id, old_fingerprint_id),
        )
        conn.execute("DELETE FROM students WHERE fingerprint_id = ?", (old_fingerprint_id,))
        conn.execute(
            "UPDATE students SET student_no = ?, student_name = ?, grade = ?, section = ?, updated_date = ? WHERE fingerprint_id = ?",
            (student_no, student_name, grade, section, now, new_fingerprint_id),
        )
        conn.commit()
        return True, "OK"
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        log.error(f"Fingerprint migration integrity error: {exc}")
        return False, "Could not migrate the student fingerprint record."
    finally:
        conn.close()


def delete_student(fingerprint_id: int) -> None:
    """Remove a student record.

    SECURITY FIX: this used to have no authorization awareness of its own.
    Both GUIs call this as part of their delete flow, but the "delete"
    permission check only ever happened over in cmd_delete() - the call
    that sends DELETE:<id> to the ESP32 - which is a *separate* step. The
    Qt students page called this database function unconditionally, before
    even checking whether cmd_delete() succeeded; the legacy GUI only ran
    cmd_delete() at all when a device happened to be connected, so a
    disconnected session skipped permission checking entirely. Either way,
    a role without "delete" permission could still permanently remove a
    student row. This enforces the same "delete" permission at the actual
    destructive operation, so it can't be bypassed by any caller - reusing
    core.permissions, not a new role system.
    """
    from core.permissions import require_permission

    if not require_permission("delete"):
        raise PermissionError("Current role does not have permission to delete students.")

    conn = get_connection()
    try:
        conn.execute(
            "UPDATE attendance SET fingerprint_id = 0 WHERE fingerprint_id = ?",
            (fingerprint_id,),
        )
        conn.execute("DELETE FROM students WHERE fingerprint_id = ?", (fingerprint_id,))
        conn.commit()
    finally:
        conn.close()


def clear_all_students() -> int:
    students = get_all_students()
    conn = get_connection()
    try:
        conn.execute("DELETE FROM attendance")
        conn.execute("DELETE FROM students WHERE fingerprint_id > 0")
        conn.commit()
        return len(students)
    finally:
        conn.close()


def get_student(fingerprint_id: int) -> Optional[StudentRow]:
    if fingerprint_id <= 0:
        return None

    conn = get_connection()
    try:
        select_sql = _student_select_sql(conn)
        row = conn.execute(
            f"SELECT {select_sql} FROM students WHERE fingerprint_id = ?",
            (fingerprint_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def has_persisted_records() -> bool:
    """Return whether the database already contains student or attendance rows.

    This is used only to prevent a missing settings file on a data-bearing
    installation from being mistaken for a clean first launch when an older
    install has no initialization marker yet.
    """
    with get_connection() as conn:
        # ID 0 is a permanent "Unregistered/Unknown" placeholder inserted
        # by init_database() on every clean install. It is schema infrastructure,
        # not evidence that a school has enrolled students or recorded attendance.
        row = conn.execute(
            "SELECT 1 FROM students WHERE fingerprint_id > 0 LIMIT 1"
        ).fetchone()
        if row is not None:
            return True
        row = conn.execute("SELECT 1 FROM attendance LIMIT 1").fetchone()
        return row is not None
    return False


def has_linked_rfid_cards() -> bool:
    """Return whether the roster has any non-empty RFID card links.

    A missing AES-GCM key must not be silently regenerated if persisted
    student records already reference cards that may have been encrypted by
    the old key. A genuinely empty/new database has no links and is safe.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'students'")
        if cursor.fetchone() is None or not _student_card_uid_column_exists(cursor):
            return False
        row = conn.execute(
            "SELECT 1 FROM students WHERE card_uid IS NOT NULL AND TRIM(card_uid) <> '' LIMIT 1"
        ).fetchone()
        return row is not None
    except sqlite3.OperationalError as exc:
        if "no such table: students" in str(exc).lower():
            return False
        raise
    finally:
        conn.close()


def get_student_by_card_uid(uid: Any) -> Optional[StudentRow]:
    normalized = normalize_card_uid(uid)
    if not normalized:
        return None

    conn = get_connection()
    try:
        cursor = conn.cursor()
        if not _student_card_uid_column_exists(cursor):
            return None
        select_sql = _student_select_sql(conn)
        row = conn.execute(
            f"SELECT {select_sql} FROM students WHERE card_uid = ?",
            (normalized,),
        ).fetchone()
        return dict(row) if row else None
    except sqlite3.OperationalError as exc:
        if "no such column: card_uid" in str(exc).lower():
            return None
        raise
    finally:
        conn.close()


def bind_student_card(fingerprint_id: int, card_uid: Any) -> Tuple[bool, str]:
    normalized = normalize_card_uid(card_uid)
    if not normalized:
        return False, "Card UID is required."

    conn = get_connection()
    try:
        if not _student_card_uid_column_exists(conn.cursor()):
            return False, "Card UID support is not enabled in this database."

        student = conn.execute(
            "SELECT fingerprint_id, student_no, student_name, card_uid FROM students WHERE fingerprint_id = ?",
            (fingerprint_id,),
        ).fetchone()
        if student is None:
            return False, "Student not found."

        existing = conn.execute(
            "SELECT fingerprint_id, student_no, student_name FROM students WHERE card_uid = ? AND fingerprint_id != ?",
            (normalized, fingerprint_id),
        ).fetchone()
        if existing:
            return False, f"This card is already registered to {existing['student_name']} (LRN {existing['student_no']}). Registration blocked."

        current_uid = student["card_uid"]
        if current_uid == normalized:
            return True, "This card is already registered to this student."

        conn.execute(
            "UPDATE students SET card_uid = ? WHERE fingerprint_id = ?",
            (normalized, fingerprint_id),
        )
        conn.commit()
        return True, "Card registered."
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        log.error(f"bind_student_card integrity error: {exc}")
        return False, "This card is already registered to another student."
    except sqlite3.OperationalError as exc:
        if "no such column: card_uid" in str(exc).lower():
            return False, "Card UID support is not enabled in this database."
        raise
    finally:
        conn.close()


def clear_student_card(fingerprint_id: int) -> Tuple[bool, str]:
    conn = get_connection()
    try:
        affected = conn.execute(
            "UPDATE students SET card_uid = NULL WHERE fingerprint_id = ?",
            (fingerprint_id,),
        )
        conn.commit()
        return (affected.rowcount > 0), "Student card cleared."
    finally:
        conn.close()


def get_all_students() -> List[StudentRow]:
    conn = get_connection()
    try:
        # fingerprint_id 0 is the reserved "Unregistered" placeholder used to
        # satisfy the attendance table's FK for unknown-fingerprint scans
        # (see init_database()) - it is not a real enrolled student.
        select_sql = _student_select_sql(conn)
        rows = conn.execute(
            f"SELECT {select_sql} FROM students WHERE fingerprint_id > 0 ORDER BY fingerprint_id"
        ).fetchall()
        return _row_dicts(rows)
    finally:
        conn.close()


def get_student_count() -> int:
    conn = get_connection()
    try:
        return conn.execute("SELECT COUNT(*) FROM students WHERE fingerprint_id > 0").fetchone()[0]
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
        # A qualifying scan records arrival only. Repeated scans remain in the
        # audit trail but never imply departure; Time-Out is a separate,
        # explicitly authorized event recorded by mark_attendance_time_out().
        already_present_today = conn.execute(
            """
            SELECT 1 FROM attendance
            WHERE fingerprint_id = ? AND date = ?
              AND LOWER(TRIM(status)) IN ('good match', 'present', 'logged', 'ok')
            LIMIT 1
            """,
            (fingerprint_id, date_str),
        ).fetchone()
        event_type = "scan" if already_present_today else "time_in"

        conn.execute(
            """
            INSERT INTO attendance (fingerprint_id, date, time, confidence, status, timestamp, event_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (fingerprint_id, date_str, time_str, confidence, status, timestamp, event_type),
        )
        conn.commit()



def mark_attendance_time_out(
    fingerprint_id: int,
    now: Optional[datetime] = None,
) -> Tuple[bool, str]:
    """Record an explicit departure; repeated biometric/RFID scans never call this."""
    try:
        student_id = int(fingerprint_id)
    except (TypeError, ValueError):
        return False, "A valid student ID is required."
    if student_id < 1:
        return False, "A registered student must be selected."

    now = now or datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    timestamp = now.isoformat()
    with get_connection() as conn:
        # Serialize concurrent departure requests so two bridge calls cannot
        # both pass the duplicate check before either inserts the event.
        conn.execute("BEGIN IMMEDIATE")
        student = conn.execute(
            "SELECT 1 FROM students WHERE fingerprint_id = ? LIMIT 1", (student_id,)
        ).fetchone()
        if not student:
            return False, "Student was not found."
        time_in = conn.execute(
            """SELECT 1 FROM attendance WHERE fingerprint_id = ? AND date = ?
               AND LOWER(TRIM(status)) IN ('good match', 'present', 'logged', 'ok')
               LIMIT 1""",
            (student_id, date_str),
        ).fetchone()
        if not time_in:
            return False, "Time In must be recorded before Time Out."
        already_out = conn.execute(
            """SELECT 1 FROM attendance WHERE fingerprint_id = ? AND date = ?
               AND event_type = 'time_out' AND UPPER(TRIM(status)) = 'TIME OUT'
               LIMIT 1""",
            (student_id, date_str),
        ).fetchone()
        if already_out:
            return False, "Time Out has already been recorded for today."
        conn.execute(
            """INSERT INTO attendance
               (fingerprint_id, date, time, confidence, status, timestamp, event_type)
               VALUES (?, ?, ?, 0, 'TIME OUT', ?, 'time_out')""",
            (student_id, date_str, time_str, timestamp),
        )
        conn.commit()
    return True, f"Time Out recorded at {time_str}."

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

    grouped: Dict[Tuple[int, str], RowDict] = {}
    qualifying_statuses = {"good match", "present", "logged", "ok"}
    for row in rows:
        row_dict = dict(row)
        # Display names are not unique. Group by stable ID so two students
        # with the same name cannot have their attendance merged.
        key = (row_dict["fingerprint_id"], row_dict["date"])
        entry = grouped.setdefault(
            key,
            {
                "student_name": row_dict["student_name"],
                "student_no": row_dict["student_no"],
                "grade": row_dict["grade"],
                "section": row_dict["section"],
                "date": row_dict["date"],
                "time_in": "",
                "time_out": "",
                "match_status": row_dict["status"],
                "status": row_dict["status"],
                "_qualifying_scan_count": 0,
            },
        )

        status = str(row_dict.get("status") or "").strip()
        if row_dict.get("event_type") == "time_out" and status.upper() == "TIME OUT":
            entry["time_out"] = row_dict["time"]
            continue
        if status.lower() in qualifying_statuses:
            # Only the first qualifying scan sets Time In. Later scans are
            # audit events, not proof of departure; only an explicit TIME OUT
            # event may populate the Time Out field.
            entry["_qualifying_scan_count"] += 1
            if entry["_qualifying_scan_count"] == 1:
                entry["time_in"] = row_dict["time"]
            entry["status"] = status
            entry["match_status"] = status

    result = list(grouped.values())
    for entry in result:
        entry.pop("_qualifying_scan_count", None)
    return result


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
    """Delete all student and attendance records.

    SECURITY FIX: this is the actual destructive operation behind the "wipe"
    workflow, but it used to have no authorization awareness of its own -
    the only thing stopping an unauthorized call was that the Qt wipe
    dialog happened to gate its *own* call behind cmd_wipe()'s permission
    check (core.permissions). Any other path that imported and called
    clear_all_data() directly - a bug, a future feature, a script run
    against this module - would bypass that check entirely, because the
    check lived one layer above the actual database operation instead of
    at the operation itself.

    This enforces the same existing "wipe" permission at the point of the
    destructive operation, so the boundary can't be bypassed by adding a
    new caller elsewhere. This does NOT introduce a new role system - it
    reuses core.permissions, the same admin/teacher/guest roles already
    used by cmd_wipe()/cmd_delete()/cmd_enroll().
    """
    from core.permissions import require_permission

    if not require_permission("wipe"):
        raise PermissionError("Current role does not have permission to clear all data.")

    conn = get_connection()
    try:
        student_count = conn.execute("SELECT COUNT(*) FROM students WHERE fingerprint_id > 0").fetchone()[0]
        attendance_count = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
        conn.execute("DELETE FROM attendance")
        conn.execute("DELETE FROM students WHERE fingerprint_id > 0")
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
            f"SELECT {_STUDENT_COLUMNS_SQL} FROM students WHERE grade = ? AND section = ? ORDER BY student_name",
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


def export_attendance_range_with_time_in_out(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """Export attendance with separate Time In and Time Out columns, sorted by student name.
    
    This function:
    1. Returns one row per student per day
    2. Includes separate time_in and time_out columns
    3. Sorts results alphabetically by student name
    4. Handles Unicode characters properly for CSV export
    """
    query = f"{ATTENDANCE_JOIN_QUERY} WHERE a.date >= ? AND a.date <= ? ORDER BY a.date ASC, a.time ASC, a.timestamp ASC"
    conn = get_connection()
    try:
        rows = conn.execute(query, (start_date, end_date)).fetchall()
        return export_attendance_rows_with_time_in_out([dict(row) for row in rows])
    finally:
        conn.close()


def export_attendance_rows_with_time_in_out(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group attendance export rows without turning weak matches into presence.

    Weak scans remain visible in the exported audit trail but do not populate
    Time In/Out. If a qualifying match exists on the same student/day, it takes
    precedence over an older weak scan.
    """
    grouped: Dict[Tuple[str, str], Dict[str, Any]] = {}
    qualifying_statuses = {"good match", "present", "logged", "ok"}
    for row_dict in rows:
        key = (row_dict["student_no"], row_dict["date"])
        status = str(row_dict.get("status") or "").strip()
        qualifies = status.lower() in qualifying_statuses
        if key not in grouped:
            grouped[key] = {
                "student_no": row_dict["student_no"],
                "student_name": row_dict["student_name"],
                "grade": row_dict["grade"],
                "section": row_dict["section"],
                "date": row_dict["date"],
                "time_in": "",
                "time_out": "",
                "confidence": row_dict.get("confidence"),
                "status": status,
                "_has_qualifying_match": False,
                "_qualifying_scan_count": 0,
            }
        entry = grouped[key]

        if row_dict.get("event_type") == "time_out" and status.upper() == "TIME OUT":
            entry["time_out"] = row_dict["time"]
            continue
        if not qualifies:
            # Retain a diagnostic status only while no qualifying event exists.
            if not entry["_has_qualifying_match"] and status:
                entry["status"] = status
                entry["confidence"] = row_dict.get("confidence")
            continue

        entry["_has_qualifying_match"] = True
        entry["status"] = status
        entry["confidence"] = row_dict.get("confidence")
        # Older event_type values were assigned from every raw scan, including
        # weak scans. Recompute time fields using qualifying scans only, so the
        # first valid scan becomes time-in even if its stored event_type says
        # time_out because an earlier weak scan existed.
        entry["_qualifying_scan_count"] += 1
        if entry["_qualifying_scan_count"] == 1:
            entry["time_in"] = row_dict["time"]

    result = list(grouped.values())
    for row in result:
        row.pop("_has_qualifying_match", None)
        row.pop("_qualifying_scan_count", None)
    result.sort(key=lambda row: (export_name_sort_key(row.get("student_name")), row.get("date", "")))
    return result

def generate_statistics_report() -> str:
    conn = get_connection()
    try:
        qualifying_sql = "LOWER(TRIM(status)) IN ('good match', 'present', 'logged', 'ok')"
        total_students = conn.execute(
            "SELECT COUNT(*) as count FROM students WHERE fingerprint_id > 0"
        ).fetchone()["count"]
        total_attendance = conn.execute(
            f"SELECT COUNT(*) as count FROM attendance WHERE {qualifying_sql}"
        ).fetchone()["count"]

        attendance_by_date = conn.execute(
            f"SELECT date, COUNT(*) as count FROM attendance WHERE {qualifying_sql} "
            "GROUP BY date ORDER BY date DESC LIMIT 30"
        ).fetchall()

        top_students = conn.execute(
            f"""
            SELECT COALESCE(s.student_name, 'Unknown') as name,
                   COUNT(a.id) as count
            FROM attendance a
            LEFT JOIN students s ON a.fingerprint_id = s.fingerprint_id
            WHERE {qualifying_sql} AND a.fingerprint_id > 0
            GROUP BY a.fingerprint_id
            ORDER BY count DESC
            LIMIT 10
            """
        ).fetchall()

        grade_stats = conn.execute(
            "SELECT grade, COUNT(*) as count FROM students WHERE fingerprint_id > 0 GROUP BY grade"
        ).fetchall()

        enrolled_students = conn.execute(
            "SELECT student_name, student_no, grade, section FROM students "
            "WHERE fingerprint_id > 0 ORDER BY student_name COLLATE NOCASE, fingerprint_id ASC"
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
        return "Unable to generate the report. Please check the application logs for more information."
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
            source = sqlite3.connect(DB_PATH, timeout=30)
            destination = sqlite3.connect(backup_path)
            try:
                source.backup(destination)
            finally:
                destination.close()
                source.close()
            log.success(f"Database backed up to {backup_path}")
            return True, f"Backup created: {backup_path.name}", str(backup_path)
        return False, 'Database file not found', None
    except Exception as exc:
        log.error(f"Database backup failed: {exc}")
        return False, "Backup failed. Please check the application logs for more information.", None


def _is_path_within_directory(path: Path, directory: Path) -> bool:
    """True if `path` is inside `directory`, using real filesystem containment.

    SECURITY FIX: this replaces a string-prefix check
    (str(backup_file).startswith(str(backup_dir))), which is not the same
    thing as directory containment. A sibling directory like
    "data/backups_evil" starts with the string "data/backups" even though
    it is NOT inside it - that check would have wrongly accepted it.

    Resolves symlinks on both sides (Path.resolve() does this) so a symlink
    planted inside the backups directory that points outside of it doesn't
    count as "inside" either.
    """
    try:
        resolved_path = path.resolve(strict=False)
        resolved_dir = directory.resolve(strict=False)
    except (OSError, RuntimeError):
        return False

    if hasattr(resolved_path, "is_relative_to"):
        return resolved_path.is_relative_to(resolved_dir)

    try:
        common = os.path.commonpath([str(resolved_path), str(resolved_dir)])
    except ValueError:
        return False
    return common == str(resolved_dir)


def _is_valid_sqlite_db_file(path: Path) -> bool:
    """Return True only when a file is a readable, structurally valid SQLite DB."""
    try:
        if not path.exists() or not path.is_file() or path.stat().st_size < 16:
            return False
        with path.open("rb") as handle:
            header = handle.read(16)
        if header != b"SQLite format 3\x00":
            return False
        connection = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
        try:
            result = connection.execute("PRAGMA quick_check").fetchone()
            return bool(result and result[0] == "ok")
        finally:
            connection.close()
    except (OSError, ValueError, sqlite3.DatabaseError):
        return False


def _has_dsis_schema(path: Path) -> bool:
    """Reject arbitrary SQLite files that are not usable DSIS database backups."""
    required_columns = {
        "students": {
            "fingerprint_id", "student_no", "student_name", "grade", "section",
            "enrollment_date", "updated_date",
        },
        "attendance": {
            "id", "fingerprint_id", "date", "time", "confidence", "status", "timestamp",
        },
    }
    try:
        connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
        try:
            tables = {
                row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            if not set(required_columns).issubset(tables):
                return False
            for table, expected in required_columns.items():
                actual = {
                    row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')
                }
                if not expected.issubset(actual):
                    return False
            return True
        finally:
            connection.close()
    except (OSError, ValueError, sqlite3.DatabaseError):
        return False


def _create_restore_safety_backup() -> Optional[Path]:
    """Create a unique, transactionally consistent safety copy of the live DB."""
    live_path = Path(DB_PATH)
    if not live_path.is_file():
        return None
    backup_dir = live_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safety_path = backup_dir / f"pre_restore_{stamp}_{os.getpid()}.db"
    suffix = 1
    while safety_path.exists():
        safety_path = backup_dir / f"pre_restore_{stamp}_{os.getpid()}_{suffix}.db"
        suffix += 1
    source = sqlite3.connect(str(live_path), timeout=30)
    destination = sqlite3.connect(str(safety_path), timeout=30)
    try:
        source.backup(destination)
    except Exception:
        destination.close()
        source.close()
        safety_path.unlink(missing_ok=True)
        raise
    else:
        destination.close()
        source.close()
    if not _is_valid_sqlite_db_file(safety_path) or not _has_dsis_schema(safety_path):
        safety_path.unlink(missing_ok=True)
        raise RuntimeError("Current database could not be preserved as a valid safety backup.")
    return safety_path


def _sqlite_backup_file(source_path: Path, destination_path: Path) -> None:
    """Copy a consistent SQLite snapshot through SQLite, including WAL content."""
    source = sqlite3.connect(f"{source_path.resolve().as_uri()}?mode=ro", uri=True, timeout=30)
    destination = sqlite3.connect(str(destination_path), timeout=30)
    try:
        source.backup(destination)
        destination.commit()
    finally:
        destination.close()
        source.close()


def restore_database(backup_path: str) -> Tuple[bool, str]:
    """Safely restore a validated DSIS database backup.

    The selected backup must be inside the backups directory and contain the
    expected DSIS tables. Before modifying the live database, create a verified
    safety snapshot. If restore fails after it starts, attempt to roll back to
    that snapshot before returning an error.
    """
    live_path = Path(DB_PATH)
    safety_backup: Optional[Path] = None
    restore_started = False
    live_database_existed = live_path.exists()
    try:
        backup_file = Path(backup_path).resolve()
        backup_dir = (live_path.parent / "backups").resolve()

        if not _is_path_within_directory(backup_file, backup_dir):
            log.error("Restore attempted from outside backups directory")
            return False, "Invalid backup file location. Backups must be in the backups directory."
        if not backup_file.exists():
            return False, "Backup file not found."
        if backup_file.suffix.lower() != ".db":
            return False, "Invalid file type. Only .db backup files are supported."
        if not _is_valid_sqlite_db_file(backup_file):
            return False, "Invalid backup file. The selected .db file is not a valid SQLite database."
        if not _has_dsis_schema(backup_file):
            return False, "Invalid backup file. It does not contain the required DSIS database schema."

        live_path.parent.mkdir(parents=True, exist_ok=True)
        safety_backup = _create_restore_safety_backup() if live_path.exists() else None

        restore_started = True
        _sqlite_backup_file(backup_file, live_path)

        if not _is_valid_sqlite_db_file(live_path) or not _has_dsis_schema(live_path):
            raise RuntimeError("Restored database failed integrity or schema validation")

        log.success(f"Database restored from {backup_file.name}")
        return True, "Database restored successfully"
    except Exception as exc:
        log.error(f"Database restore failed: {exc}")
        if restore_started and safety_backup is not None:
            try:
                _sqlite_backup_file(safety_backup, live_path)
                if not _is_valid_sqlite_db_file(live_path) or not _has_dsis_schema(live_path):
                    raise RuntimeError("Recovered database did not pass validation")
                return False, "Restore failed. The original database was recovered from its pre-restore safety backup."
            except Exception as recovery_exc:
                log.error(f"Pre-restore database recovery failed: {recovery_exc}")
                return False, "Restore and automatic recovery failed. Preserve the pre-restore safety backup and contact support."
        if safety_backup is None:
            if live_database_existed:
                return False, (
                    "Restore stopped because a verified safety snapshot could not "
                    "be created. The existing database was not restored over; "
                    "check logs before retrying."
                )
            if restore_started:
                # Remove incomplete files from a failed first-time restore.
                for candidate in (live_path, Path(f"{live_path}-wal"), Path(f"{live_path}-shm")):
                    try:
                        candidate.unlink(missing_ok=True)
                    except OSError as cleanup_exc:
                        log.error(f"Could not remove incomplete restore artifact {candidate}: {cleanup_exc}")
            return False, (
                "Restore failed. No pre-restore safety backup was available because "
                "no existing database was present. Check logs before retrying."
            )
        return False, "Restore failed. Check logs and the pre-restore safety backup before retrying."

def list_backups() -> List[RowDict]:
    try:
        backup_dir = Path(DB_PATH).parent / 'backups'
        if not backup_dir.exists():
            return []

        backups: List[RowDict] = []
        # Include automatic pre-restore safety snapshots so an operator can
        # manually recover one if the restore rollback itself ever fails.
        backup_files = list(backup_dir.glob('attendance_*.db'))
        backup_files.extend(backup_dir.glob('pre_restore_*.db'))
        for backup_file in sorted(backup_files, key=lambda item: item.stat().st_mtime, reverse=True):
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