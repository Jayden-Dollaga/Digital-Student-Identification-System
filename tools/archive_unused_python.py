from pathlib import Path
import shutil

root = Path(r"c:\Users\EnforcerX\Downloads\Arduino-IDE - Project\AI-Assisted Fingerprint Attendance System\python")
archive_root = root / "testing_area"
archive_root.mkdir(parents=True, exist_ok=True)

items_to_move = [
    Path("core/database_addition_snippet.py"),
    Path("gui/legacy/app_test.py"),
    Path("gui/legacy/app_test1.py"),
    Path("gui/legacy/bfeas_app.py"),
    Path("gui/legacy/bfeas_app2.py"),
    Path("gui/legacy/reports_table_page.py"),
    Path("services/backup.py"),
    Path("services/excel_export.py"),
]

moved = []
for rel in items_to_move:
    src = root / rel
    if not src.exists():
        continue
    dst = archive_root / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    moved.append(str(rel))

for dirpath in [root / "gui" / "legacy"]:
    if dirpath.exists() and dirpath.is_dir() and not any(dirpath.iterdir()):
        dirpath.rmdir()

print("MOVED")
for item in moved:
    print(item)
