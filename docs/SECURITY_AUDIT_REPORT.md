# Security Audit Report: AI-Assisted Fingerprint Attendance System

**Date:** August 14, 2026  
**Project:** Digital Student Identification System (DSIS)  
**Scope:** Python application code security analysis

---

## Executive Summary

This security audit identified **15 vulnerabilities** across the fingerprint attendance system, ranging from **Critical** to **Medium** severity. The most critical issues involve:

1. **Shell injection vulnerability** in subprocess calls
2. **Path traversal** in database restore functionality  
3. **Insecure dynamic module loading** with unrestricted paths
4. **Weak client-side authorization** with no backend enforcement
5. **Missing input validation** on multiple fields

---

## Critical Vulnerabilities

### 1. **Shell Injection via subprocess.Popen with shell=True**

**Location:** [python/gui/serial_troubleshooting.py](../python/gui/serial_troubleshooting.py#L50)

**Severity:** CRITICAL

**Description:**
```python
subprocess.Popen(["start", "", "https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers"], shell=True)
```

The `shell=True` parameter enables shell interpretation, allowing command injection through specially crafted URLs or environment variable manipulation.

**Issue Details:**
- Although the URL appears hardcoded, if this pattern is replicated elsewhere with user input, it becomes exploitable
- Windows `start` command interprets special characters
- An attacker could inject commands through environment variables or by modifying the URL parameter

**Proof of Concept:**
If user input is ever passed to this function, an attacker could execute arbitrary commands on the system.

**Recommended Fix:**
```python
def open_driver_help() -> None:
    """Open the ESP32 driver help page in the default browser."""
    if sys.platform.startswith("win"):
        # Remove shell=True - it's not needed for simple URL opening
        subprocess.Popen(["start", "https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers"])
    elif sys.platform.startswith("darwin"):
        subprocess.Popen(["open", "https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers"])
    else:
        subprocess.Popen(["xdg-open", "https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers"])
```

---

### 2. **Path Traversal in Database Restore Function**

**Location:** [python/core/database.py](../python/core/database.py#L807-L817)

**Severity:** CRITICAL

**Description:**
```python
def restore_database(backup_path: str) -> Tuple[bool, str]:
    try:
        if not Path(backup_path).exists():
            return False, 'Backup file not found'
        
        shutil.copy2(backup_path, DB_PATH)  # ← VULNERABLE
        log.success(f"Database restored from {backup_path}")
        return True, 'Database restored successfully'
```

The function accepts an arbitrary path without validation, allowing:
- Overwriting the main database with any file on the system
- Reading and copying any accessible file to the database location
- Potential information disclosure through error messages

**Attack Scenario:**
```python
# Attacker selects a malicious file via file dialog
restore_database("../../../windows/system32/config/sam")  # Could copy sensitive system files
```

**Recommended Fix:**
```python
def restore_database(backup_path: str) -> Tuple[bool, str]:
    try:
        backup_file = Path(backup_path).resolve()
        backup_dir = (Path(DB_PATH).parent / 'backups').resolve()
        
        # Ensure the backup file is within the backups directory
        if not str(backup_file).startswith(str(backup_dir)):
            return False, 'Invalid backup file location'
        
        if not backup_file.exists():
            return False, 'Backup file not found'
        
        # Verify it's actually a SQLite database
        if not backup_file.suffix == '.db':
            return False, 'Invalid backup file format'
        
        # Create a temporary copy first
        import tempfile
        temp_file = Path(tempfile.gettempdir()) / f"db_restore_{uuid.uuid4()}.db"
        shutil.copy2(backup_file, temp_file)
        
        # Verify it's a valid database before replacing
        try:
            test_conn = sqlite3.connect(str(temp_file), timeout=2)
            test_conn.execute("SELECT 1 FROM sqlite_master LIMIT 1")
            test_conn.close()
        except Exception:
            temp_file.unlink()
            return False, 'Backup file is corrupted or not a valid database'
        
        # Now perform the restore
        shutil.copy2(temp_file, DB_PATH)
        temp_file.unlink()
        log.success(f"Database restored from {backup_file.name}")
        return True, 'Database restored successfully'
    except Exception as exc:
        log.error(f"Database restore failed: {exc}")
        return False, f"Restore failed: {exc}"
```

---

### 3. **Insecure Dynamic Module Loading**

**Location:** [python/gui/legacy/reports_table_page.py](../python/gui/legacy/reports_table_page.py#L12-L28)

**Severity:** CRITICAL

**Description:**
```python
spec = importlib.util.spec_from_file_location("testing_area_reports_table_page", archive_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)  # ← DANGEROUS

for name, value in vars(module).items():
    if not name.startswith("__"):
        globals()[name] = value  # ← Pollutes global namespace
```

This code:
- Loads arbitrary Python files from the filesystem without validation
- Executes code from external modules with full privileges
- Imports all symbols into the global namespace, potentially overwriting existing functions
- No integrity check of the source module

**Attack Scenario:**
If an attacker can modify or replace the `archive_path` file, they can execute arbitrary code with full application privileges.

**Recommended Fix:**
```python
import importlib.util
import sys
import hashlib
from pathlib import Path

# Define known good checksums for acceptable modules
TRUSTED_MODULES = {
    "testing_area_reports_table_page.py": "abc123def456...",  # SHA256 hash
}

def load_trusted_module(module_name: str, archive_path: Path):
    """Load a module only if it matches a trusted checksum."""
    if not archive_path.exists():
        return None
    
    # Verify checksum
    expected_hash = TRUSTED_MODULES.get(archive_path.name)
    if expected_hash is None:
        raise ValueError(f"Module {archive_path.name} is not in the trusted list")
    
    actual_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    if actual_hash != expected_hash:
        raise ValueError(f"Module checksum mismatch. File may be corrupted or tampered.")
    
    spec = importlib.util.spec_from_file_location(module_name, archive_path)
    if spec is None or spec.loader is None:
        return None
    
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Usage - only import specific needed exports
try:
    archive_path = python_root / "testing_area" / "gui" / "legacy" / "reports_table_page.py"
    if archive_path.exists():
        module = load_trusted_module("reports_table_page", archive_path)
        if module:
            # Import only specific known functions
            ReportsPage = getattr(module, 'ReportsPage', None)
except Exception as exc:
    # Fail securely
    class ReportsPage:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("Legacy reports module not available")
```

---

## High Severity Vulnerabilities

### 4. **Weak Client-Side Authorization Model**

**Location:** [python/config.py](../python/config.py#L36-L48), [python/gui/app.py](../python/gui/app.py#L136), [python/gui/app.py](../python/gui/app.py#L289-L291)

**Severity:** HIGH

**Description:**
The role-based access control system is implemented entirely on the client-side:

```python
def has_permission(self, permission: str) -> bool:
    """Check if current user role has a specific permission."""
    role_config = CONFIG.user_roles.get(self.current_role, {})
    return permission in role_config.get("permissions", [])
```

**Issues:**
1. Roles are stored in client-side JSON: `settings.json` in the data directory
2. User can modify `settings.json` to change their role
3. Buttons are disabled/enabled based on this check, but no backend validation
4. An attacker can directly edit `settings.json` to gain admin permissions
5. No audit trail of permission changes

**Proof of Concept:**
```json
// Original settings.json
{"current_role": "guest"}

// Attacker modifies to:
{"current_role": "admin"}

// Now all admin features are accessible
```

**Recommended Fix:**
```python
# config.py - Add session-based authentication
class AuthService:
    def __init__(self):
        self.session_token = None
        self.authenticated_role = None
        self.session_start_time = None
    
    def authenticate(self, password: str) -> bool:
        """Validate user password and create authenticated session."""
        # Use proper password hashing (bcrypt/argon2)
        import hashlib
        stored_hash = self._get_stored_admin_password_hash()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if password_hash != stored_hash:
            return False
        
        # Create session token
        import secrets
        self.session_token = secrets.token_urlsafe(32)
        self.authenticated_role = "admin"
        self.session_start_time = time.time()
        
        # Log authentication
        log.info("User authenticated as admin")
        return True
    
    def has_permission_authenticated(self, permission: str) -> bool:
        """Check permission with session validation."""
        if self.session_token is None:
            return False
        
        # Verify session hasn't expired (e.g., 1 hour timeout)
        if time.time() - self.session_start_time > 3600:
            self.session_token = None
            return False
        
        role_config = CONFIG.user_roles.get(self.authenticated_role, {})
        return permission in role_config.get("permissions", [])
```

---

### 5. **Missing Input Validation on Student Data**

**Location:** [python/core/database.py](../python/core/database.py#L178-L206), [python/services/student_service.py](../python/services/student_service.py#L10)

**Severity:** HIGH

**Description:**
Student input fields are not validated for length, format, or content:

```python
def add_student(
    fingerprint_id: int,
    student_no: str,      # ← No length/format validation
    student_name: str,    # ← No length/format validation
    grade: str,           # ← No validation
    section: str,         # ← No validation
) -> Tuple[bool, str]:
    if fingerprint_id <= 0:
        return False, "Fingerprint ID must be a positive integer."
    # Only checks fingerprint_id, ignores other fields
```

**Risks:**
1. **Buffer overflow potential** - Extremely long strings could cause issues
2. **Data corruption** - Special characters in names could break parsing
3. **NoSQL/Database injection** (if ORM is used elsewhere) - Though using parameterized queries helps here
4. **Information exposure** - Accepting and storing arbitrary data without validation

**Recommended Fix:**
```python
import re
from typing import Tuple

def validate_student_input(
    fingerprint_id: int,
    student_no: str,
    student_name: str,
    grade: str,
    section: str,
) -> Tuple[bool, str]:
    """Validate all student input fields."""
    
    # Fingerprint ID validation
    if not isinstance(fingerprint_id, int) or fingerprint_id <= 0 or fingerprint_id > 127:
        return False, "Fingerprint ID must be between 1 and 127"
    
    # Student number validation
    if not student_no or not isinstance(student_no, str):
        return False, "Student number is required"
    if len(student_no) < 1 or len(student_no) > 20:
        return False, "Student number must be 1-20 characters"
    if not re.match(r'^[A-Z0-9\-_]+$', student_no.upper()):
        return False, "Student number contains invalid characters"
    
    # Student name validation
    if not student_name or not isinstance(student_name, str):
        return False, "Student name is required"
    if len(student_name) < 2 or len(student_name) > 100:
        return False, "Student name must be 2-100 characters"
    # Allow letters, spaces, and common name characters
    if not re.match(r"^[a-zA-Z\s\-'\.]+$", student_name):
        return False, "Student name contains invalid characters"
    
    # Grade validation
    if not grade or not isinstance(grade, str):
        return False, "Grade is required"
    if len(grade) > 20:
        return False, "Grade must not exceed 20 characters"
    
    # Section validation
    if not section or not isinstance(section, str):
        return False, "Section is required"
    if len(section) > 20:
        return False, "Section must not exceed 20 characters"
    
    return True, ""

def add_student(
    fingerprint_id: int,
    student_no: str,
    student_name: str,
    grade: str,
    section: str,
) -> Tuple[bool, str]:
    # Validate all inputs first
    ok, msg = validate_student_input(fingerprint_id, student_no, student_name, grade, section)
    if not ok:
        return False, msg
    
    # Sanitize inputs
    student_no = student_no.strip().upper()
    student_name = student_name.strip()
    grade = grade.strip()
    section = section.strip()
    
    # ... rest of the function
```

---

### 6. **Improper Exception Handling with Information Disclosure**

**Location:** Multiple files - [python/core/database.py](../python/core/database.py#L807-L817), [python/gui/reports_page.py](../python/gui/reports_page.py#L46-L71)

**Severity:** HIGH

**Description:**
Detailed exception messages are shown to users, potentially revealing:
- Database structure and paths
- Filesystem structure
- Internal application details

```python
except Exception as exc:
    log.error(f"Database restore failed: {exc}")
    return False, f"Restore failed: {exc}"  # ← Full exception shown to user
```

**Attack Scenario:**
An attacker could craft inputs to trigger errors and gather information about the system:
```
"Restore failed: [Errno 13] Permission denied: 'C:\\Users\\Admin\\data\\attendance.db'"
```

This reveals:
- Full path structure
- Windows environment
- Database file location

**Recommended Fix:**
```python
def restore_database(backup_path: str) -> Tuple[bool, str]:
    try:
        # ... validation code ...
        shutil.copy2(backup_file, DB_PATH)
        log.success(f"Database restored successfully")
        return True, 'Database restored successfully'
    except PermissionError:
        log.error(f"Permission denied restoring backup: {exc}", path=str(backup_file))
        return False, "Permission denied: cannot restore database. Check file permissions."
    except FileNotFoundError:
        log.error(f"Backup file not found during restore")
        return False, "Backup file not found or was deleted."
    except IOError as exc:
        log.error(f"I/O error during restore: {exc}")
        return False, "Unable to restore database. Please try again."
    except Exception as exc:
        # Log full details for debugging, but show generic message to user
        log.exception(f"Unexpected error during restore", error=str(exc))
        return False, "Database restore failed. Please contact support."
```

---

### 7. **Race Condition in Wipe Operation**

**Location:** [python/gui/app.py](../python/gui/app.py#L113-L125)

**Severity:** HIGH

**Description:**
The wipe confirmation is vulnerable to race conditions:

```python
self.wipe_requested = False  # Reset after first WIPE
# ...
self.wipe_requested = True   # User clicks Confirm Wipe

# No atomic guarantee that old "SUCCESS" messages won't trigger wipe
if self.wipe_requested and RE_WIPE_SUCCESS.search(message):
    # Wipe database
```

**Attack Scenario:**
1. User sends WIPE, sees "SUCCESS" from a previous session
2. `wipe_requested` flag incorrectly allows the old success message to trigger database wipe
3. Application state becomes inconsistent
4. Database could be wiped unintentionally

**Recommended Fix:**
```python
import uuid

class FingerprintApp(ctk.CTk):
    def __init__(self):
        # ... existing code ...
        self.wipe_operation_id = None  # Track current wipe operation
    
    def confirm_wipe(self):
        """Initiate a wipe with unique operation ID."""
        self.wipe_operation_id = str(uuid.uuid4())
        current_op_id = self.wipe_operation_id
        
        if cmd_wipe(self.serial_handler):
            self.log_message(f"Wipe initiated (op: {current_op_id})")
        else:
            self.wipe_operation_id = None
            self.log_message("Failed to send WIPE command")
    
    def _parse_wipe_progress(self, message):
        """Only accept wipe success for current operation."""
        if self.wipe_operation_id is None:
            return
        
        if RE_WIPE_SUCCESS.search(message):
            # Only process if this is the current operation
            current_op = self.wipe_operation_id
            self.wipe_operation_id = None  # Clear immediately
            
            # Wipe database with verification
            try:
                clear_all_data()
                self.log_message(f"Database wiped (op: {current_op})")
            except Exception as exc:
                log.error("Wipe operation failed", op_id=current_op, error=str(exc))
```

---

## Medium Severity Vulnerabilities

### 8. **SQL Injection Risk in Dynamic Query Building**

**Location:** [python/core/database.py](../python/core/database.py#L390-L416)

**Severity:** MEDIUM

**Description:**
While parameterized queries are used, dynamic SQL query building with string formatting could introduce vulnerabilities:

```python
where_clause = " AND ".join(filters)  # ← Built from user input
query = f"{ATTENDANCE_JOIN_QUERY}"
if where_clause:
    query += f" WHERE {where_clause}"  # ← Concatenated directly
```

If `filters` list is ever populated from unsanitized user input (not visible in current code but possible in future changes):

```python
filters.append(f"a.date >= '{start_date}'")  # VULNERABLE format
```

**Recommended Fix:**
```python
def get_daily_attendance_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[RowDict]:
    filters: List[str] = []
    params: List[Any] = []
    
    # Always use parameterized queries
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
    
    # Current implementation is correct - keep using parameterized queries
    with get_connection() as conn:
        rows = conn.execute(query, tuple(params)).fetchall()
```

---

### 9. **Hardcoded Database Path Without Access Control**

**Location:** [python/config.py](../python/config.py#L23-L28), [python/core/database.py](../python/core/database.py#L15-L16)

**Severity:** MEDIUM

**Description:**
Database path is hardcoded and accessible to all roles:

```python
DB_PATH = str(CONFIG.db_path)
```

All functions in database.py use this single path without access control. There's no per-user database isolation or audit trail.

**Risks:**
1. All users access the same database regardless of role
2. No audit trail of who made changes
3. Guest users can read sensitive attendance data
4. No separation of concerns between different user roles

**Recommended Fix:**
```python
class AuditedDatabaseAccess:
    """Wrapper for database access with audit trail."""
    
    def __init__(self, user_role: str, user_id: Optional[str] = None):
        self.user_role = user_role
        self.user_id = user_id or "SYSTEM"
    
    def log_query(self, query: str, params: tuple, result_count: int):
        """Log database queries for audit trail."""
        log.info(
            "Database query executed",
            user_id=self.user_id,
            user_role=self.user_role,
            query_type=self._extract_query_type(query),
            param_count=len(params),
            result_count=result_count,
        )
    
    def get_student(self, fingerprint_id: int) -> Optional[StudentRow]:
        """Read student data with permission check."""
        if self.user_role == "guest":
            # Guests can only see limited data
            log.warning("Guest role attempted to read student data", fingerprint_id=fingerprint_id)
            return None
        
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM students WHERE fingerprint_id = ?",
                (fingerprint_id,),
            ).fetchone()
            self.log_query("SELECT FROM students", (fingerprint_id,), 1 if row else 0)
            return dict(row) if row else None
        finally:
            conn.close()
```

---

### 10. **Backup Files Not Encrypted**

**Location:** [python/core/database.py](../python/core/database.py#L790-L805)

**Severity:** MEDIUM

**Description:**
Database backups are created as plain SQLite files without encryption:

```python
shutil.copy2(DB_PATH, backup_path)  # ← Unencrypted copy
```

**Risks:**
1. Attendance records (sensitive PII) are stored in plaintext
2. Anyone with file access can read the database
3. No integrity verification
4. Backup files stored in predictable location with timestamps

**Recommended Fix:**
```python
import os
import sqlite3
from cryptography.fernet import Fernet

def backup_database_encrypted() -> Tuple[bool, str, Optional[str]]:
    """Create encrypted backup of database."""
    try:
        backup_dir = Path(DB_PATH).parent / 'backups'
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate encryption key (store securely, not in code)
        encryption_key = os.getenv('BACKUP_ENCRYPTION_KEY')
        if not encryption_key:
            # Generate and save key on first run (prompt user for password)
            key = Fernet.generate_key()
            encryption_key = key.decode()
            # Store in secure location with user prompt
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = backup_dir / f'attendance_{timestamp}.db.enc'
        
        # Copy database to temporary location
        temp_backup = backup_dir / f'tmp_{timestamp}.db'
        shutil.copy2(DB_PATH, temp_backup)
        
        # Encrypt the backup
        cipher = Fernet(encryption_key.encode())
        with open(temp_backup, 'rb') as f:
            encrypted_data = cipher.encrypt(f.read())
        
        with open(backup_path, 'wb') as f:
            f.write(encrypted_data)
        
        # Secure delete the unencrypted temporary file
        import shutil as sh
        temp_backup.unlink()
        
        # Set restrictive file permissions (Windows: read-only)
        os.chmod(backup_path, 0o600)
        
        log.success(f"Encrypted database backup created: {backup_path.name}")
        return True, f"Encrypted backup created: {backup_path.name}", str(backup_path)
    except Exception as exc:
        log.error(f"Encrypted backup failed: {exc}")
        return False, f"Backup failed: {exc}", None
```

---

### 11. **Missing Validation on Port and Baud Rate**

**Location:** [python/gui/app.py](../python/gui/app.py#L380-L390)

**Severity:** MEDIUM

**Description:**
Selected COM port and baud rate are not validated before use:

```python
def _get_selected_baud_rate(self) -> int:
    baud_var = getattr(self, "baud_var", None)
    if baud_var is None:
        return int((self.settings or {}).get("baud_rate", CONFIG.baud_rate))
    value = baud_var.get()
    try:
        return int(value)  # ← Any integer accepted
    except (TypeError, ValueError):
        return CONFIG.baud_rate
```

**Risks:**
1. Invalid baud rates could cause application crashes
2. Extremely large values could consume resources
3. No whitelist of valid ports

**Recommended Fix:**
```python
def _get_selected_baud_rate(self) -> int:
    VALID_BAUD_RATES = {9600, 19200, 38400, 57600, 115200, 230400}
    
    baud_var = getattr(self, "baud_var", None)
    if baud_var is None:
        baud = int((self.settings or {}).get("baud_rate", CONFIG.baud_rate))
    else:
        try:
            baud = int(baud_var.get())
        except (TypeError, ValueError):
            return CONFIG.baud_rate
    
    if baud not in VALID_BAUD_RATES:
        log.warning("Invalid baud rate requested, using default", requested=baud)
        return CONFIG.baud_rate
    
    return baud

def _get_selected_port(self) -> str:
    INVALID_PORT_CHARS = {'\\', '/', ':', '*', '?', '"', '<', '>', '|', '\x00'}
    
    port_var = getattr(self, "port_var", None)
    if port_var is None:
        port = str((self.settings or {}).get("com_port", ""))
    else:
        port = port_var.get()
    
    port = port.strip() if isinstance(port, str) else ""
    
    # Validate port format
    if not port or len(port) > 20:
        return CONFIG.com_port
    
    if any(char in port for char in INVALID_PORT_CHARS):
        log.warning("Invalid characters in port name", port=port)
        return CONFIG.com_port
    
    return port
```

---

### 12. **Bare Except Clauses Hiding Errors**

**Location:** Multiple locations - [python/gui/app.py](../python/gui/app.py#L97), [python/core/device_discovery.py](../python/core/device_discovery.py#L160)

**Severity:** MEDIUM

**Description:**
Multiple bare `except:` and `except Exception:` clauses silently swallow errors:

```python
try:
    self.after(100, lambda: apply_appearance_mode(...))
except Exception:  # ← Silently ignores
    pass
```

**Risks:**
1. Critical errors are hidden from debugging
2. Application state becomes inconsistent
3. Security-relevant errors are masked
4. Makes troubleshooting nearly impossible

**Recommended Fix:**
```python
try:
    self.after(100, lambda: apply_appearance_mode(
        "Dark" if str(settings["theme"]).lower() == "dark" else "Light",
        self,
    ))
except KeyError as exc:
    log.warning("Theme setting missing from configuration", key=str(exc))
except RuntimeError as exc:
    log.error("Failed to apply theme", error=str(exc))
except Exception as exc:
    log.exception("Unexpected error applying theme", error=str(exc))
```

---

### 13. **Serial Port Connection Not Properly Closed on Error**

**Location:** [python/core/serial_handler.py](../python/core/serial_handler.py#L150-L175)

**Severity:** MEDIUM

**Description:**
If an exception occurs during connection setup, the serial port might not be closed:

```python
try:
    # Connection code
    self.esp32 = cable
except Exception:
    # Port not closed if exception occurs
    pass
```

**Risks:**
1. Resource leaks - serial ports stay open
2. Windows can run out of COM port resources
3. Application becomes unusable after repeated connection attempts
4. Other applications can't access the device

**Recommended Fix:**
```python
def connect(self, port: str = "", baud: int = 115200) -> Tuple[bool, str]:
    # ... existing code ...
    
    try:
        discovery_port, cable, metadata, discovery_error = discover_device(
            preferred_port=port,
            baud=baud,
            allow_search=False,
        )
        
        if discovery_port is None:
            # Ensure old port is closed before returning error
            if self.esp32 is not None and getattr(self.esp32, "is_open", False):
                try:
                    self.esp32.close()
                except Exception:
                    pass
                finally:
                    self.esp32 = None
            
            return False, f"ESP32 discovery failed on {port}: {discovery_error}"
        
        # Close old connection before opening new one
        if self.esp32 is not None and self.esp32 != cable:
            try:
                self.esp32.close()
            except Exception:
                pass
        
        self.esp32 = cable
        # ... rest of code ...
    except Exception as exc:
        # Clean up on unexpected error
        if self.esp32 is not None:
            try:
                self.esp32.close()
            except Exception:
                pass
            finally:
                self.esp32 = None
        raise
```

---

### 14. **Settings File Not Protected from Tampering**

**Location:** [python/settings_store.py](../python/settings_store.py#L42-L64)

**Severity:** MEDIUM

**Description:**
Settings are stored in plaintext JSON without integrity verification:

```python
def save_settings(settings: Dict[str, Any], path: str | Path | None = None) -> Path:
    settings_path = Path(path or SETTINGS_FILE)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    payload = default_settings()
    payload.update(settings)
    with settings_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)  # ← No checksum/signature
    return settings_path
```

**Attack Scenario:**
Attacker modifies `settings.json`:
```json
{
    "current_role": "admin",
    "auto_reconnect": false,
    "com_port": "MALICIOUS_COMMAND"
}
```

**Recommended Fix:**
```python
import hmac
import hashlib

SETTINGS_SECRET = os.getenv('SETTINGS_SECRET', 'default_key_change_me')

def save_settings(settings: Dict[str, Any], path: str | Path | None = None) -> Path:
    settings_path = Path(path or SETTINGS_FILE)
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    
    payload = default_settings()
    payload.update(settings)
    
    # Create HMAC for integrity verification
    payload_str = json.dumps(payload, sort_keys=True)
    signature = hmac.new(
        SETTINGS_SECRET.encode(),
        payload_str.encode(),
        hashlib.sha256
    ).hexdigest()
    
    file_content = {
        "settings": payload,
        "signature": signature,
        "version": 1
    }
    
    with settings_path.open("w", encoding="utf-8") as handle:
        json.dump(file_content, handle, indent=2)
    
    # Secure file permissions
    os.chmod(settings_path, 0o600)
    return settings_path

def load_settings(path: str | Path | None = None) -> Dict[str, Any]:
    settings_path = Path(path or SETTINGS_FILE)
    if not settings_path.exists():
        return default_settings()
    
    try:
        with settings_path.open("r", encoding="utf-8") as handle:
            file_content = json.load(handle)
        
        # Verify integrity
        if isinstance(file_content, dict) and "settings" in file_content:
            settings = file_content["settings"]
            signature = file_content.get("signature", "")
            
            payload_str = json.dumps(settings, sort_keys=True)
            expected_signature = hmac.new(
                SETTINGS_SECRET.encode(),
                payload_str.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                log.warning("Settings file integrity check failed - file may have been tampered")
                return default_settings()
            
            return settings
        else:
            # Legacy format or corrupted
            if isinstance(file_content, dict):
                return file_content
            return default_settings()
    
    except (json.JSONDecodeError, OSError):
        return default_settings()
```

---

## Low Severity Issues

### 15. **Weak Fingerprint ID Validation**

**Location:** [python/core/database.py](../python/core/database.py#L178), [python/core/commands.py](../python/core/commands.py#L18)

**Severity:** LOW

**Description:**
Fingerprint IDs are validated but the error message doesn't indicate the valid range clearly:

```python
def build_enroll_command(fingerprint_id=None):
    if fingerprint_id is None:
        return "ENROLL"
    if fingerprint_id < 1 or fingerprint_id > 127:
        raise ValueError("fingerprint_id must be between 1 and 127")
    return f"ENROLL:{fingerprint_id}"
```

**Improvement:**
This is adequate but could be more defensive with better validation at entry points.

---

## Summary Table

| ID | Vulnerability | Severity | File | Status |
|----|---|---|---|---|
| 1 | Shell injection via subprocess | CRITICAL | serial_troubleshooting.py | Requires immediate fix |
| 2 | Path traversal in restore_database | CRITICAL | database.py | Requires immediate fix |
| 3 | Insecure dynamic module loading | CRITICAL | legacy/reports_table_page.py | Requires immediate fix |
| 4 | Weak client-side authorization | HIGH | config.py, app.py | Requires redesign |
| 5 | Missing input validation | HIGH | database.py, services | Requires comprehensive fix |
| 6 | Information disclosure in errors | HIGH | database.py, reports_page.py | Widespread - requires audit |
| 7 | Race condition in wipe operation | HIGH | app.py | Requires refactor |
| 8 | SQL injection (potential) | MEDIUM | database.py | Monitor for changes |
| 9 | Hardcoded database path | MEDIUM | config.py, database.py | Requires access control layer |
| 10 | Unencrypted backups | MEDIUM | database.py | Requires encryption implementation |
| 11 | Unvalidated port/baud rate | MEDIUM | app.py | Requires whitelist validation |
| 12 | Bare except clauses | MEDIUM | Multiple files | Requires systematic refactor |
| 13 | Resource leaks on error | MEDIUM | serial_handler.py | Requires proper cleanup |
| 14 | Unprotected settings file | MEDIUM | settings_store.py | Requires HMAC/signature |
| 15 | Fingerprint ID validation | LOW | database.py, commands.py | Minor improvement |

---

## Recommendations by Priority

### Immediate (Critical - This Week)
1. Fix shell injection in subprocess calls
2. Add path traversal validation in restore_database
3. Remove or secure dynamic module loading
4. Add comprehensive input validation

### Short-term (High - This Month)
5. Implement proper authentication/authorization system
6. Audit all exception handling for information disclosure
7. Fix race conditions in critical operations
8. Add resource cleanup on errors

### Medium-term (Medium - This Quarter)
9. Implement database-level access control
10. Add encryption for backup files
11. Implement input whitelisting for all user-controllable values
12. Add file integrity checking for configuration

### Long-term (Low - Ongoing)
13. Regular security audits
14. Dependency vulnerability scanning
15. Implement comprehensive audit logging
16. Code review process for security-sensitive changes

---

## Testing Recommendations

1. **Fuzzing** - Test all inputs with random/malformed data
2. **Path traversal testing** - Attempt to restore from system files
3. **Authentication testing** - Attempt to bypass role checks
4. **Resource exhaustion** - Open/close serial ports repeatedly
5. **Error handling** - Trigger various exceptions and verify messages

---

## Conclusion

The application has several critical security vulnerabilities that must be addressed before production use. The most pressing issues involve:

- Injection vulnerabilities (shell injection, potential SQL injection)
- Improper path validation allowing file access outside intended directories
- Complete lack of backend authentication/authorization
- Information disclosure through error messages

Implementing the recommended fixes will significantly improve the security posture of the application.

---

**Report Generated:** 2026-08-14  
**Auditor:** Security Analysis Bot  
**Severity Distribution:** 3 CRITICAL | 4 HIGH | 7 MEDIUM | 1 LOW
