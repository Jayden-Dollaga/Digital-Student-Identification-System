###############################################################################
#  services/backup.py
#  AS608 Fingerprint Attendance System
#
#  Simple database backup — copies the .db file to data/backups/
###############################################################################

import os
import shutil
from datetime import datetime
from pathlib import Path

from config import get_config

CONFIG = get_config()
BACKUP_FOLDER = Path(CONFIG.db_path).parent / "backups"


def backup_database():
    """
    Copy the database file to the backups folder with a timestamp.
    Returns (True, filepath) on success or (False, error message).
    """
    try:
        os.makedirs(BACKUP_FOLDER, exist_ok=True)
        ts       = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"attendance_backup_{ts}.db"
        dest     = os.path.join(BACKUP_FOLDER, filename)
        shutil.copy2(DB_PATH, dest)
        return True, dest
    except Exception as e:
        return False, str(e)
