# Paste this into core/database.py, e.g. right after get_attendance_by_date().
# It groups scans per student per day so the Reports page can show a single
# row per student/day with Time-In (earliest scan) and Time-Out (latest scan) —
# matching the web report's layout even though your raw table stores one row per scan.

def get_daily_attendance_summary(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Get one summarized row per (student, date) within [start_date, end_date] inclusive.
    time_in  = earliest scan time that day
    time_out = latest scan time that day
    scan_count = how many scans happened that day (1 means no separate time-out)
    Dates in 'YYYY-MM-DD' format.
    """
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            a.fingerprint_id,
            CASE WHEN a.fingerprint_id = 0 THEN 'Unregistered' ELSE COALESCE(s.student_no, 'N/A') END AS student_no,
            CASE WHEN a.fingerprint_id = 0 THEN 'Unregistered' ELSE COALESCE(s.student_name, 'Unknown ID:' || a.fingerprint_id) END AS student_name,
            CASE WHEN a.fingerprint_id = 0 THEN 'N/A' ELSE COALESCE(s.grade, 'N/A') END AS grade,
            CASE WHEN a.fingerprint_id = 0 THEN 'N/A' ELSE COALESCE(s.section, 'N/A') END AS section,
            a.date,
            MIN(a.time) AS time_in,
            MAX(a.time) AS time_out,
            COUNT(*) AS scan_count
        FROM attendance a
        LEFT JOIN students s ON a.fingerprint_id = s.fingerprint_id
        WHERE a.date BETWEEN ? AND ?
        GROUP BY a.fingerprint_id, a.date
        ORDER BY a.date DESC, student_name ASC
    """, (start_date, end_date)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
