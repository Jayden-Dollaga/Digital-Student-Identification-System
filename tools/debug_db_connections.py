import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
import core.database as db

orig_connect = sqlite3.connect
open_conns = []


def tracked_connect(*args, **kwargs):
    conn = orig_connect(*args, **kwargs)
    open_conns.append(conn)
    print('opened', len(open_conns), conn)
    # Do NOT attempt to monkey-patch built-in sqlite3.Connection.close
    # (it's a read-only attribute implemented in C). Instead, we keep
    # a list of connections and close them manually at the end of the
    # script to ensure no open connections remain.
    return conn


sqlite3.connect = tracked_connect

print('init')
db.init_database()
print('student_count', db.get_student_count())
print('attendance_count', db.get_attendance_count_today())
print('attendance_today', db.get_attendance_today())
print('remaining', len(open_conns))
for conn in list(open_conns):
    try:
        conn.close()
    except Exception:
        pass
# Clear the tracking list since we've closed them explicitly
open_conns.clear()
print('after manual close', len(open_conns))
