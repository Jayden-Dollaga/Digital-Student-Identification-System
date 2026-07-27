"""Persistence layer for students, attendance events, reports, and backup helpers.

This module centralizes SQLite access for the fingerprint attendance system and
keeps the rest of the application focused on workflow logic instead of raw SQL.
"""

import os
import shutil
import sqlite3
from datetime import datetime
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
        a.status
    FROM attendance a
    LEFT JOIN students s ON a.fingerprint_id = s.fingerprint_id
"""


def get_connection() -> sqlite3.Connection:
    """Open and configure a database connection."""
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _row_dicts(rows: Iterable[sqlite3.Row]) -> List[RowDict]:
    return [dict(row) for row in rows]


def init_database() -> None:
    """Create database tables and indexes if they do not already exist."""
    with get_connection() as conn:
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
                FOREIGN KEY (fingerprint_id) REFERENCES students(fingerprint_id)
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_attendance_fingerprint_id ON attendance(fingerprint_id)"
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_timestamp ON attendance(timestamp)")

        conn.execute("DELETE FROM students WHERE fingerprint_id <= 0")
        conn.commit()

    log.success(f"Database ready at {os.path.abspath(DB_PATH)}")


# -----------------------------------------------------------------------------
# Student operations
# -----------------------------------------------------------------------------


def add_student(
    fingerprint_id: int,
    student_no: str,
    student_name: str,
    grade: str,
    section: str,
) -> Tuple[bool, str]:
    if fingerprint_id <= 0:
        return False, "Fingerprint ID must be a positive integer."

    now = datetime.now().isoformat()
    try:
        with get_connection() as conn:
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


def update_student(
    fingerprint_id: int,
    student_no: str,
    student_name: str,
    grade: str,
    section: str,
) -> Tuple[bool, str]:
    now = datetime.now().isoformat()
    try:
        with get_connection() as conn:
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


def delete_student(fingerprint_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM students WHERE fingerprint_id = ?", (fingerprint_id,))
        conn.commit()


def clear_all_students() -> int:
    students = get_all_students()
    with get_connection() as conn:
        conn.execute("DELETE FROM attendance")
        conn.execute("DELETE FROM students")
        conn.commit()
    return len(students)


def get_student(fingerprint_id: int) -> Optional[StudentRow]:
    if fingerprint_id <= 0:
        return None

    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM students WHERE fingerprint_id = ?",
            (fingerprint_id,),
        ).fetchone()
    return dict(row) if row else None


def get_all_students() -> List[StudentRow]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM students ORDER BY fingerprint_id").fetchall()
    return _row_dicts(rows)


def get_student_count() -> int:
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]


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
        conn.execute(
            """
            INSERT INTO attendance (fingerprint_id, date, time, confidence, status, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (fingerprint_id, date_str, time_str, confidence, status, timestamp),
        )
        conn.commit()


def get_attendance_today() -> List[AttendanceRow]:
    today = datetime.now().strftime("%Y-%m-%d")
    query = f"{ATTENDANCE_JOIN_QUERY} WHERE a.date = ? ORDER BY a.timestamp DESC, a.id DESC"
    with get_connection() as conn:
        rows = conn.execute(query, (today,)).fetchall()
    return _row_dicts(rows)


def get_attendance_all() -> List[AttendanceRow]:
    query = f"{ATTENDANCE_JOIN_QUERY} ORDER BY a.timestamp DESC"
    with get_connection() as conn:
        rows = conn.execute(query).fetchall()
    return _row_dicts(rows)


def get_attendance_paginated(limit: int = 100, offset: int = 0) -> List[AttendanceRow]:
    query = f"{ATTENDANCE_JOIN_QUERY} ORDER BY a.timestamp DESC, a.id DESC LIMIT ? OFFSET ?"
    with get_connection() as conn:
        rows = conn.execute(query, (limit, offset)).fetchall()
    return _row_dicts(rows)


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
        entry["time_out"] = row_dict["time"]
        if str(row_dict["status"]).lower() in {"present", "logged", "ok"}:
            entry["status"] = row_dict["status"]

    return list(grouped.values())


def get_attendance_by_date(date_str: str) -> List[AttendanceRow]:
    query = f"{ATTENDANCE_JOIN_QUERY} WHERE a.date = ? ORDER BY a.time"
    with get_connection() as conn:
        rows = conn.execute(query, (date_str,)).fetchall()
    return _row_dicts(rows)


def clear_all_attendance() -> int:
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
        conn.execute("DELETE FROM attendance")
        conn.commit()
    return count


def clear_all_data() -> Tuple[int, int]:
    with get_connection() as conn:
        student_count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        attendance_count = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
        conn.execute("DELETE FROM attendance")
        conn.execute("DELETE FROM students")
        conn.commit()
    return student_count, attendance_count


def get_attendance_by_student(fingerprint_id: int) -> List[AttendanceRow]:
    query = f"{ATTENDANCE_JOIN_QUERY} WHERE a.fingerprint_id = ? ORDER BY a.date DESC, a.time DESC"
    with get_connection() as conn:
        rows = conn.execute(query, (fingerprint_id,)).fetchall()
    return _row_dicts(rows)


def get_students_by_grade_section(grade: str, section: str) -> List[StudentRow]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM students WHERE grade = ? AND section = ? ORDER BY student_name",
            (grade, section),
        ).fetchall()
    return _row_dicts(rows)


def count_attendance_by_date(date_str: str) -> int:
    with get_connection() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM attendance WHERE date = ?",
            (date_str,),
        ).fetchone()[0]


def get_attendance_statistics() -> RowDict:
    with get_connection() as conn:
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


def get_students_statistics() -> RowDict:
    with get_connection() as conn:
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


def export_attendance_range(start_date: str, end_date: str) -> List[AttendanceRow]:
    query = f"{ATTENDANCE_JOIN_QUERY} WHERE a.date >= ? AND a.date <= ? ORDER BY a.date ASC, a.time ASC"
    with get_connection() as conn:
        rows = conn.execute(query, (start_date, end_date)).fetchall()
    return _row_dicts(rows)


def generate_statistics_report() -> str:
    try:
        with get_connection() as conn:
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
    try:
        if not Path(backup_path).exists():
            return False, 'Backup file not found'

        shutil.copy2(backup_path, DB_PATH)
        log.success(f"Database restored from {backup_path}")
        return True, 'Database restored successfully'
    except Exception as exc:
        log.error(f"Database restore failed: {exc}")
        return False, f"Restore failed: {exc}"


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
