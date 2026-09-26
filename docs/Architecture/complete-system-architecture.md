# Complete DSIS System Architecture

This document is the whole-project architecture map for the maintained Digital Student Identification System (DSIS).

It is intentionally broader than the focused v3 architecture documents: it shows the repository as a connected system, from the user interface and Python backend down to the ESP32, AS608 fingerprint sensor, RC522 RFID reader, persistence, security, testing, build tooling, documentation, and historical version lineage.

> **Scope:** Current maintained architecture, with archival and test branches included for context. The documentation lineage requested for this rebuild starts at `f0b0074`; current branch HEAD is `84aea85`.
>
> **Current runtime:** v3 HTML/CSS/JavaScript UI rendered through pywebview, backed by Python and SQLite.
>
> **Current active firmware:** ESP32_DSIS_AllInOne, firmware 1.2.5, protocol 1.

---

## 1. Architecture at a glance

    ┌───────────────────────────────────────────────────────────────┐
    │             DIGITAL STUDENT IDENTIFICATION SYSTEM            │
    │                              DSIS                             │
    └───────────────────────────────────────────────────────────────┘
                                  │
          ┌───────────────────────┼────────────────────────┐
          │                       │                        │
          ▼                       ▼                        ▼
       USER / UI              SOFTWARE                 HARDWARE
          │                       │                        │
          │                       ├── Web UI              ├── ESP32
          │                       ├── API bridge          ├── AS608
          │                       ├── Core backend        └── RC522
          │                       ├── Services
          │                       ├── Database
          │                       ├── Authentication
          │                       ├── Permissions
          │                       ├── Reports
          │                       └── Settings
          │
          ▼
      IDENTIFICATION
          │
      ┌───┴──────────────────────┐
      │                          │
      ▼                          ▼
  Fingerprint                   RFID
      │                          │
      ▼                          ▼
    AS608                      RC522
      │                          │
      └──────────────┬───────────┘
                     ▼
                DEVICE EVENT
                     │
                     ▼
               SERIAL PROTOCOL
                     │
                     ▼
              PYTHON PROCESSOR
                     │
              ┌──────┴──────┐
              │             │
           Validate      Identify
              │             │
              └──────┬──────┘
                     ▼
                  SQLite
                     │
          ┌──────────┼──────────┐
          │          │          │
          ▼          ▼          ▼
       Records    Reports    Statistics
          │          │          │
          └──────────┼──────────┘
                     ▼
                   WEB UI
                     │
                     ▼
                 USER RESULT

The key architectural idea is that the identification methods converge into shared processing and persistence rather than becoming separate attendance systems.

---

# 2. Desktop application family

    Desktop Application
            │
            ├── Launchers
            │     ├── run_web_gui.py
            │     └── run_web_gui.bat
            │
            ▼
        gui_web.main_web
            │
            ├── Install exception hooks
            ├── Create Api
            ├── Initialize runtime
            ├── Initialize database
            ├── Initialize logging
            ├── Load settings
            ├── Create pywebview window
            ├── Attach API bridge
            └── Start native UI loop
            │
            ▼
       ┌───────────────────┐
       │     PYWEBVIEW     │
       │    NATIVE WINDOW  │
       └─────────┬─────────┘
                 │
                 ▼
              WEB UI
                 │
        ┌────────┼─────────────────────────────────────────┐
        │        │                │                         │
        ▼        ▼                ▼                         ▼
    index.html  app.js        styles.css                 UI STATE
        │        │
        └────────┴───────────────────────────────────────────────┐
                                                                 │
       Dashboard · Attendance · Students · Reports · Logs        │
       Settings · Calendar                                      │
                                                                 │
       Current page · Current role · Device state                │
       Scan state · Modal state                                  │
                                                                 ▼
                                                        window.pywebview.api

---

# 3. API / bridge layer

    JavaScript
        │
        ▼
    window.pywebview.api
        │
        ▼
    python/gui_web/api.py
        │
        ├── Connection operations
        │     ├── connect
        │     ├── disconnect
        │     ├── port discovery
        │     └── reconnect
        │
        ├── Student operations
        │     ├── save
        │     ├── edit
        │     ├── enrollment
        │     └── deletion
        │
        ├── Identification operations
        │     ├── fingerprint scan
        │     ├── RFID scan
        │     ├── RFID registration
        │     └── RFID erase
        │
        ├── Attendance operations
        │     ├── scan results
        │     ├── attendance records
        │     └── evaluation
        │
        ├── Reporting
        │     ├── reports
        │     ├── CSV preparation
        │     └── chart generation
        │
        ├── Calendar
        │     ├── holidays
        │     ├── suspensions
        │     └── schedule exceptions
        │
        ├── Settings
        │     ├── device settings
        │     ├── attendance rules
        │     └── UI settings
        │
        ├── Authentication
        │     ├── login
        │     ├── password setup
        │     └── session state
        │
        └── Live UI events
              ├── scan_result
              ├── serial_line
              ├── log_line
              ├── enroll_progress
              ├── delete_progress
              ├── wipe_progress
              ├── fingerprint_count
              ├── connection_status
              ├── data_changed
              └── mode_changed

The bridge is the integration boundary: the frontend presents state and requests operations; the Python backend owns validation, permissions, device control, persistence, and business logic.

---

# 4. Python core backend family

    python/core/
          │
          ├── database
          │     ├── SQLite initialization
          │     ├── Schema creation/migration
          │     ├── Student CRUD
          │     ├── RFID UID linking
          │     ├── Attendance logging
          │     ├── Queries and summaries
          │     ├── Reports
          │     ├── CSV preparation
          │     ├── Charts
          │     ├── Backup
          │     ├── Restore
          │     └── Destructive data operations
          │
          ├── serial_handler
          │     ├── COM management
          │     ├── Serial connection
          │     ├── Read/write
          │     ├── Line buffering
          │     ├── Device state
          │     ├── Disconnect handling
          │     └── Auto reconnect
          │
          ├── device_discovery
          │     ├── Enumerate COM ports
          │     ├── Rank candidates
          │     ├── Probe device
          │     ├── Send ID?
          │     ├── Validate device identity
          │     └── Validate protocol version
          │
          ├── commands
          │     ├── SCAN
          │     ├── STOP
          │     ├── ENROLL
          │     ├── DELETE
          │     ├── WIPE
          │     ├── LIST
          │     ├── CARD_WRITE_HEX
          │     └── CARD_ERASE
          │
          ├── attendance
          │     ├── Parse serial lines
          │     ├── Parse JSON events
          │     ├── Fingerprint processing
          │     ├── RFID processing
          │     ├── Unknown handling
          │     ├── Confidence classification
          │     ├── UID normalization
          │     ├── AES-GCM validation
          │     ├── Cooldown handling
          │     └── Attendance persistence
          │
          ├── attendance_status
          │     ├── Time-in evaluation
          │     ├── Time-out evaluation
          │     ├── Early calculation
          │     ├── Late calculation
          │     └── Absent rules
          │
          ├── attendance_calendar
          │     ├── Holidays
          │     ├── Suspensions
          │     ├── Half-days
          │     ├── Weekday exclusions
          │     └── Date-specific schedule
          │
          ├── auth
          │     ├── Password creation
          │     ├── Password verification
          │     ├── Salt generation
          │     └── PBKDF2-HMAC-SHA256
          │
          ├── permissions
          │     ├── Guest
          │     ├── Teacher
          │     ├── Administrator
          │     ├── Role hierarchy
          │     ├── Permission checks
          │     ├── Session locking
          │     └── Session timeout
          │
          ├── rfid_card
          │     ├── AES key creation
          │     ├── AES key storage
          │     ├── UID normalization
          │     ├── Payload construction
          │     ├── AES-GCM encryption
          │     ├── AES-GCM decryption
          │     ├── Authentication-tag validation
          │     ├── Payload-version validation
          │     └── Student identity extraction
          │
          ├── logger
          │     ├── Console logging
          │     ├── File logging
          │     ├── UI log buffering
          │     └── Runtime diagnostics
          │
          ├── setup_wizard
          │     ├── Password step
          │     ├── Device step
          │     ├── Schedule step
          │     ├── Branding step
          │     └── Resume state
          │
          ├── firmware_helper
          │     ├── Firmware discovery
          │     └── Build/upload helpers
          │
          └── utils
                ├── JSON helpers
                ├── Date/time helpers
                └── Shared conversion utilities

---

# 5. Service family

    python/services/
           │
           ├── student_service.py
           │      └── Student operations
           │
           └── attendance_service.py
                  └── Attendance operations
                           │
                           ▼
                       Core layer

These services are intentionally thin wrappers around the core backend.

---

# 6. Hardware family

    ┌───────────────────────────────┐
    │        ESP32 WROOM-32         │
    │       DSIS All-In-One         │
    └───────────────┬───────────────┘
                    │
       ┌────────────┼────────────┐
       │            │            │
       ▼            ▼            ▼
    USB Serial    UART 2       SPI bus
     115200       57600
       │            │            │
       ▼            ▼            ▼
    Windows PC     AS608       RC522
       │
       ▼
    Python DSIS application

Communication boundaries:

    PC ↔ ESP32  : 115200 baud
    ESP32 ↔ AS608: 57600 baud
    ESP32 ↔ RC522: SPI
    PC never talks directly to AS608 or RC522.

---

# 7. ESP32 firmware family

    firmware/ESP32_DSIS_AllInOne/
                    │
                    ▼
           ESP32_DSIS_AllInOne.ino
                    │
        ┌───────────┼───────────────────────┐
        │           │                       │
        ▼           ▼                       ▼
   Host interface  Fingerprint engine     RFID engine
        │           │                       │
        ├── ID?     ├── getImage()          ├── Detect card
        ├── SCAN    ├── image2Tz()          ├── Read UID
        ├── STOP    ├── fingerSearch()      ├── Detect family
        ├── ENROLL  ├── createModel()       ├── Authenticate
        ├── DELETE  ├── storeModel()        ├── Read payload
        ├── WIPE    ├── loadModel()         ├── Write payload
        ├── LIST    ├── deleteModel()       └── Verify readback
        ├── STATUS  └── template count
        ├── CARD_WRITE_HEX
        └── CARD_ERASE
                    │
                    ▼
              Structured JSON
                    │
                    ▼
              USB serial output

The firmware owns physical sensor interaction and the host serial protocol. It does not own student names, attendance history, application roles, or the SQLite database.

---

# 8. Fingerprint family

    ┌──────────┐
    │   AS608  │
    └────┬─────┘
         │
     ┌───┴─────────────────────────┐
     │                             │
     ▼                             ▼
  ENROLLMENT                    ATTENDANCE
     │                             │
     ▼                             ▼
 Find free ID                   Place finger
     │                             │
     ▼                             ▼
 Capture finger #1             getImage()
     │                             │
     ▼                             ▼
 image2Tz(1)                  image2Tz()
     │                             │
     ▼                             ▼
 Remove finger                    │
     │                             ▼
     ▼                         Search DB / device
 Capture finger #2                 │
     │                        ┌────┴─────────┐
     ▼                        │              │
 image2Tz(2)                MATCH        NO MATCH
     │                        │              │
     ▼                        ▼              ▼
 createModel()            Confidence      UNKNOWN
     │                    classification
     ├──────────────┐         │
     │              │         ├── ≥ desktop threshold
   SUCCESS        FAILURE     │
     │              │         └── < desktop threshold
     ▼              ▼
 storeModel()     Error
     │
     ▼
 Enrollment event
     │
     ▼
 Python save_student()
     │
     ▼
 SQLite

Fingerprint identifiers are 1–127. ID 0 is reserved for the durable Unregistered / Unknown identity.

Firmware and desktop confidence filtering are separate. The firmware has its own acceptance floor; the desktop applies the configured minimum confidence for classification.

---

# 9. RFID family

    ┌──────────┐
    │   RC522  │
    └────┬─────┘
         │
         ▼
   Read UID + PICC type
         │
         ▼
    CardDetector
         │
     ┌───┼──────────────────────────────┐
     │   │                              │
     ▼   ▼                              ▼
 Classic  Type 2                     Other
     │   │                              │
     │   ├── Ultralight profile         ├── MIFARE Plus
     │   ├── NTAG215                    ├── DESFire / ISO14443-4
     │   └── NTAG216                    ├── Ambiguous 144B Type 2
     │                                  └── Unknown / unsupported
     │
     ├── MIFARE Mini
     ├── MIFARE 1K
     └── MIFARE 4K
            │
            ▼
      Family-specific adapter
        │                  │
        ▼                  ▼
   ClassicAdapter       Type2Adapter
        │                  │
        ▼                  ▼
   Authenticate        Read pages 4–15
   Read blocks          Write pages
   Write blocks         Verify readback
   Verify readback
        │                  │
        └────────┬─────────┘
                 ▼
             48-byte payload
                 │
                 ▼
           Python RFID layer

Current supported writable profiles are MIFARE Classic Mini/1K/4K plus the supported 48-byte Type 2 path for compatible Ultralight, NTAG215, and NTAG216 cards. Some detected families remain detection-only or unsupported because the installed reader/library interface cannot positively distinguish or safely operate them.

The detector and adapters are concrete firmware components selected by card family; this is modular behavior even though the project is not built around a formal abstract adapter interface.

---

# 10. RFID cryptographic payload

    RFID card
       │
       ▼
    48-byte DSIS envelope
       │
       ├── Payload version
       ├── Random 12-byte nonce
       └── AES-GCM ciphertext + authentication tag
                │
                ▼
          Encrypted plaintext
                │
                ├── Fingerprint ID
                └── Length-prefixed student number
                         │
                         ▼
                 UID-bound AAD
                         │
                         ▼
                    Authentication

The normalized card UID is authenticated as associated data, so the payload is bound to the physical card UID.

The application generates an AES key and stores it in the local settings data. A card must authenticate successfully before its identity payload is trusted.

---

# 11. RFID attendance family

    RC522
      │
      ▼
   Detect card
      │
      ▼
   Get UID
      │
      ▼
   CardDetector
      │
    ┌─┴───────────────┐
    │                 │
 Supported         Unsupported
    │                 │
    ▼                 ▼
 Adapter            UNKNOWN /
    │               unreadable
    ▼
 Read 48-byte payload
    │
    ▼
 JSON card event
    │
    ▼
 USB Serial 115200
    │
    ▼
 SerialHandler
    │
    ▼
 AttendanceProcessor
    │
    ├── Normalize UID
    │
    ├── Validate payload length/version
    │
    ├── AES-GCM decrypt
    │
    ├── Validate authentication tag
    │
    ├── Extract fingerprint ID
    │
    ├── Extract student number
    │
    ├── Lookup student
    │
    ├── Compare DB student number
    │
    ├── Compare DB card UID
    │
    └── Apply attendance cooldown
             │
       ┌─────┴──────────────┐
       │                    │
     FAIL                  PASS
       │                    │
       ▼                    ▼
    UNKNOWN             Log attendance
                             │
                             ▼
                           SQLite

An invalid or tampered RFID payload is not treated as a valid student match merely because the UID is known.

---

# 12. RFID registration family

    Select Student
         │
         ▼
 start_rfid_register_session()
         │
    ┌────┼──────────────────────────────┐
    │    │                              │
 Permission  Student exists          No conflict
    │    │                              │
    └────┴──────────────┬───────────────┘
                       ▼
                  Start card mode
                       │
                       ▼
                    Tap card
                       │
                       ▼
                     Read UID
                       │
                       ▼
               Check existing owner
                       │
                ┌──────┴──────┐
                │             │
              Linked       Available
                │             │
                ▼             ▼
              Reject      Build payload
                              │
                              ▼
                         AES-GCM encrypt
                              │
                              ▼
                          UID-bound AAD
                              │
                              ▼
                         48-byte envelope
                              │
                              ▼
                      CARD_WRITE_HEX
                              │
                              ▼
                             ESP32
                              │
                 ┌────────────┴────────────┐
                 │                         │
              Classic                    Type 2
                 │                         │
           Write blocks               Write pages
                 │                         │
                 └────────────┬────────────┘
                              ▼
                        Readback verify
                              │
                              ▼
                    Python verification
                              │
               ┌──────────────┼────────────────┐
               │              │                │
            UID match    Payload match    Verified flag
               │              │                │
               └──────────────┴────────────────┘
                              │
                              ▼
                      db.bind_student_card()
                              │
                              ▼
                       Student ↔ Card UID

The local student-to-card binding is committed only after the physical card write has been verified.

---

# 13. Enrollment family

    Student information
           │
           ▼
      Validate input
           │
           ▼
       start_enroll()
           │
           ├── Permission check
           ├── Conflict check
           └── Stop active scan
           │
           ▼
         ENROLL
           │
           ▼
          ESP32
           │
           ├── Find free fingerprint ID
           ├── Ask for first capture
           ├── Ask for second capture
           ├── Create model
           └── Store template
           │
      ┌────┴──────────┐
      │               │
   FAILURE         SUCCESS
      │               │
      ▼               ▼
     Error       Enrollment event
                      │
                      ▼
                 Python receives ID
                      │
                      ▼
                 save_student()
                      │
                      ▼
                    SQLite

The database record is created after device-side enrollment succeeds, reducing the chance of a local record referring to a fingerprint template that was never stored.

---

# 14. Shared attendance family

    IDENTIFICATION
          │
      ┌───┴───────────┐
      │               │
      ▼               ▼
  Fingerprint       RFID
      │               │
      ▼               ▼
     AS608           RC522
      │               │
      └──────┬────────┘
             ▼
      AttendanceProcessor
             │
        ┌────┴─────────────┐
        │                  │
   Known identity     Unknown identity
        │                  │
        ▼                  ▼
   Cooldown check        UNKNOWN
        │
     ┌──┴───────┐
     │          │
  Blocked     Allowed
     │          │
     ▼          ▼
   Ignore      Record event
                    │
              ┌─────┴─────┐
              │           │
            time_in     time_out
              │           │
              └─────┬─────┘
                    ▼
             attendance table

This shared path is what makes multiple identification methods possible without duplicating the complete attendance stack.

---

# 15. Delete family

    Delete Student
         │
         ▼
    Permission check
         │
         ▼
    DELETE:<fingerprint>
         │
         ▼
        ESP32
         │
      ┌──┴────────┐
      │           │
   EXISTS       MISSING
      │           │
      ▼           ▼
  Delete model   FAILED
      │
      ▼
   SUCCESS
      │
      ▼
 Local database cleanup
      │
      ├── Remove student record
      └── Preserve historical attendance by remapping to ID 0
                         │
                         ▼
               Unregistered / Unknown

Delete is device-first: successful device deletion precedes the local student cleanup.

---

# 16. Wipe family

    WIPE REQUEST
          │
     ┌────┴───────────────┐
     │                    │
 DEVICE DOMAIN        LOCAL DOMAIN
     │                    │
     ▼                    ▼
 ESP32 wipe           Permission check
     │                    │
     ▼                    ▼
 Clear fingerprint     Clear local data
 templates                 │
     │                     ├── Attendance
     ▼                     └── Students
 Device success                 │
     │                          ▼
     └──────────────┬───────────┘
                    ▼
              ID 0 remains
                    │
                    ▼
             Unregistered

Device storage and local application data are separate destruction domains. A partial failure is reported rather than silently treating both sides as complete.

---

# 17. Database family

    data/attendance.db
             │
       ┌─────┴─────────────┐
       │                   │
       ▼                   ▼
    students            attendance
       │                   │
       ├── fingerprint_id  ├── id
       ├── student_no      ├── fingerprint_id
       ├── student_name    ├── date
       ├── grade           ├── time
       ├── section         ├── confidence
       ├── card_uid        ├── status
       ├── enrollment_date ├── timestamp
       └── updated_date    └── event_type
              │
              │ fingerprint_id
              └──────────────────────────────► attendance.fingerprint_id

Special identity:

    ID 0     = Unregistered / Unknown
    ID 1–127 = AS608 fingerprint IDs

Database responsibilities include:

    ├── SQLite initialization
    ├── Schema migration
    ├── Foreign-key enforcement
    ├── Busy-timeout / connection handling
    ├── Student validation
    ├── Student CRUD
    ├── Card UID linking
    ├── Attendance logging
    ├── Reports and summaries
    ├── Backup
    └── Restore

---

# 18. Settings family

    data/settings.json
            │
      ┌─────┼─────────────────────────────┐
      │     │                             │
      ▼     ▼                             ▼
   DEVICE ATTENDANCE                     UI
      │       │                           │
      ├── com_port                        ├── theme
      ├── baud_rate                       ├── branding
      ├── auto_detect                      └── sidebar state
      └── auto_reconnect
              │
              ├── cooldown
              ├── min_confidence
              ├── time_in
              ├── time_out
              ├── early threshold
              ├── late threshold
              └── absent threshold
            │
       ┌────┼─────────────┐
       │    │             │
       ▼    ▼             ▼
   CALENDAR BACKUP      SETUP STATE
       │      │             │
       ├── holidays         ├── device done
       ├── suspensions      ├── schedule done
       ├── half-days        └── branding done
       └── weekday rules
            │
            ▼
        AUTH DATA
            │
            └── password hash / salt / iteration data

The active role is held in memory. Any stored role information is for display/setup continuity and is not the authoritative authorization source.

---

# 19. Authentication family

    FIRST RUN
       │
       ▼
   Create password
       │
       ▼
   Generate random salt
       │
       ▼
 PBKDF2-HMAC-SHA256
       │
       ▼
 Save authentication data
       │
       ▼
 Administrator session
       │
       ▼
 Normal application runtime
       │
      SESSION
       │
   ┌───┼───────────┐
   │   │           │
   ▼   ▼           ▼
 Guest Teacher   Admin
   │   │           │
   └───┼───────────┘
       ▼
 Permission check
       │
    ┌──┴──────┐
    │         │
  ALLOW     DENY
    │         │
    ▼         ▼
 Continue    Error
    │
    ▼
 Idle timeout
    │
    ▼
 Session changes / locks

The backend permission checks are authoritative; frontend visibility is convenience only.

---

# 20. Reporting family

    SQLite data
         │
         ▼
    Reporting layer
         │
    ┌────┼─────────────────────┐
    │    │                     │
    ▼    ▼                     ▼
 REPORTS STATISTICS         EVALUATION
    │    │                     │
    ├── Daily              ├── Day
    ├── Weekly             ├── Week
    └── Monthly            └── Month
         │
         ├── Total students
         ├── Attendance totals
         ├── By grade
         ├── By section
         └── Attendance timeline
                │
        ┌───────┴────────┐
        │                │
       CSV             Charts
        │                │
        └───────┬────────┘
                ▼
            Export files

---

# 21. Backup family

    attendance.db
         │
         ▼
   backup_database()
         │
         ▼
    data/backups/
         │
         ▼
 attendance_TIMESTAMP.db
         │
         ▼
       RESTORE
         │
      ┌──┴───────────────┐
      │                  │
 Validate path      Validate SQLite
      │                  │
      └────────┬─────────┘
               ▼
           Replace DB
               │
               ▼
      data/attendance.db

Backup and restore are local filesystem operations. Restore validation is performed before replacement.

---

# 22. Logging family

    core.logger
          │
      ┌───┼───────────────────┐
      │   │                   │
      ▼   ▼                   ▼
   Console File             UI buffer
      │    │                   │
      │    ▼                   ▼
      │ data/logs/          log_line events
      │
      ├── startup
      ├── device
      ├── serial
      ├── attendance
      ├── security
      ├── errors
      └── diagnostics

Centralized logging provides both human-readable runtime output and diagnostic history.

---

# 23. Runtime thread family

    DSIS PROCESS
          │
    ┌─────┼────────────────────────┐
    │     │                        │
    ▼     ▼                        ▼
  Main UI  Serial reader       Background workers
    │       │                        │
    │       ├── Read ESP32 lines     ├── Auto backup
    │       ├── Buffer complete lines └── Auto reconnect
    │       └── Parse events
    │               │
    │               ▼
    │      AttendanceProcessor
    │
    ▼
  pywebview
    │
    ▼
  app.js

The runtime is a desktop process, not a collection of separate web servers or cloud services.

---

# 24. Runtime data family

    data/
      │
      ├── attendance.db
      │     └── Students + attendance history
      │
      ├── settings.json
      │     └── Configuration + authentication data
      │
      ├── backups/
      │     └── Database snapshots
      │
      ├── logs/
      │     └── Runtime logs
      │
      ├── exports/
      │     └── Generated report exports
      │
      ├── charts/
      │     └── Generated report graphics
      │
      └── .admin_initialized
            └── First-admin setup marker

The runtime data directory is local application state and should not be populated with real student data in a public development repository.

---

# 25. Testing family

    tests/
       │
       ├── UNIT / BACKEND
       │     ├── Attendance
       │     ├── Database
       │     ├── Authentication
       │     ├── Permissions
       │     ├── Serial
       │     ├── Settings
       │     ├── RFID
       │     ├── Logs
       │     └── Validation
       │
       ├── GUI / WEB
       │     ├── Web GUI smoke
       │     ├── Responsive UI
       │     ├── Enrollment dialogs
       │     └── Student pages
       │
       ├── HARDWARE / FIRMWARE
       │     ├── ESP32 smoke
       │     ├── Serial tests
       │     ├── Sensor failure paths
       │     └── Active firmware protocol
       │
       ├── INTEGRATION
       │     ├── GUI ↔ API
       │     ├── API ↔ database
       │     ├── API ↔ serial
       │     └── API ↔ RFID
       │
       └── SPECIAL REGRESSION AREAS
             ├── Security
             ├── Error handling
             ├── Protocol compatibility
             ├── Database reset/restore
             └── Project structure

The tests act as regression coverage for the software, GUI, serial protocol, RFID behavior, and physical-device integration.

---

# 26. Build family

    Build/
       │
       ├── DSIS_v1.spec
       ├── DSIS_v2.spec
       └── DSIS_v3.spec
              │
              ▼
          ACTIVE BUILD
              │
              ▼
           PyInstaller
              │
              ▼
       Windows distribution

Supporting specifications and packaging helpers live alongside the versioned build specifications.

---

# 27. Tools family

    tools/
       │
       ├── Database tools
       │     ├── DB refactor
       │     ├── DB connection/debug helpers
       │     └── Archive utilities
       │
       ├── Serial tools
       │     ├── Port probes
       │     ├── Pipeline testers
       │     └── Worker probes
       │
       ├── Runtime tools
       │     ├── Runtime manager
       │     ├── GUI startup verifier
       │     └── Verification scripts
       │
       └── Forensics / diagnostics
             └── Search and investigation utilities

These tools support development, diagnosis, verification, and repository maintenance; they are not all part of the normal end-user runtime.

---

# 28. Firmware family and history

    firmware/
         │
         ├── ACTIVE
         │     └── ESP32_DSIS_AllInOne
         │            ├── AS608
         │            ├── RC522
         │            ├── LED manager
         │            ├── command engine
         │            ├── scan engine
         │            └── JSON protocol
         │
         ├── EARLIER
         │     └── ESP32_Fingerprint_AllInOne
         │
         └── TEST SKETCHES
               ├── attendance
               ├── delete
               ├── enroll
               ├── rc522_test
               ├── rc522_read
               ├── rc522_write
               ├── rc522_readwrite
               ├── rc522_dumpinfo_test
               └── fingerprint_check

The active all-in-one firmware is the maintained device path. Earlier firmware and small sketches remain useful for historical reference, experiments, and hardware diagnosis.

---

# 29. Documentation family

    docs/
      │
      ├── Architecture
      │     ├── Complete System Architecture   ← this document
      │     ├── v3 System Architecture
      │     ├── Runtime Contract
      │     ├── Software Flow
      │     ├── Database Schema
      │     ├── Data and Settings
      │     └── pywebview Bridge
      │
      ├── Hardware
      │     ├── Wiring
      │     ├── Hardware connections
      │     ├── Active firmware
      │     ├── Serial protocol
      │     ├── Drivers and ports
      │     └── Firmware variants
      │
      ├── User Guide
      │     ├── Installation
      │     ├── Workflows
      │     ├── Enrollment and scanning
      │     ├── Attendance rules
      │     ├── Roles and permissions
      │     ├── First-run wizard
      │     └── Backup / restore / export
      │
      ├── Development
      │     ├── Setup
      │     ├── Testing
      │     ├── Logging
      │     ├── Runtime data
      │     ├── Release/build
      │     ├── Change log
      │     └── Documentation authority
      │
      ├── Troubleshooting
      ├── Security
      ├── API
      ├── History
      ├── Overview
      └── generated / research / investigations

---

# 30. Repository family

    Digital-Student-Identification-System/
                   │
      ┌────────────┼───────────────────────────────────────────┐
      │            │                                           │
      ▼            ▼                                           ▼
   Runtime      Support                                      History
      │            │                                           │
      ├── python/  ├── tests/                                  └── archive/
      ├── firmware/├── tools/
      ├── data/   ├── Build/
      ├── docs/   └── root launchers
      └── requirements.txt
                   │
                   └── README / installation / release / security

Historical UI material lives under archive/legacy-ui/ and is not the supported launch path.

---

# 31. Version lineage

    DSIS
      │
      ├───────────────────────┬─────────────────────────────┐
      │                       │                             │
      ▼                       ▼                             ▼
     V1                      V2                            V3
      │                       │                             │
 CustomTkinter           PySide6 / Qt              HTML + JS
      │                       │                             │
      │                       │                          pywebview
      │                       │                             │
      └───────────────────────┴───────────────┬─────────────┘
                                              ▼
                                      Python backend
                                              │
                            ┌─────────────────┼────────────────┐
                            │                 │                │
                            ▼                 ▼                ▼
                         Database          Serial         Attendance
                            │                 │                │
                            └─────────────────┼────────────────┘
                                              ▼
                                        Current DSIS v3

V1 and V2 are preserved as lineage/reference material. V3 is the maintained runtime architecture.

---

# 32. Complete data flow

    STUDENT / STAFF ACTION
             │
             ▼
          WEB UI
             │
             ▼
     pywebview API bridge
             │
             ▼
          Api class
             │
       ┌─────┼───────────────────┐
       │     │                   │
       ▼     ▼                   ▼
  Permissions Core logic        Serial
       │     │                   │
       │     │                   ▼
       │     │                 ESP32
       │     │                   │
       │     │            ┌──────┴───────┐
       │     │            │              │
       │     │            ▼              ▼
       │     │          AS608           RC522
       │     │            │              │
       │     │            └──────┬───────┘
       │     │                   ▼
       │     │            Structured event
       │     │                   │
       │     └───────────────────┤
       │                         ▼
       │                AttendanceProcessor
       │                   │            │
       │                   ▼            ▼
       │              Fingerprint      RFID
       │                                │
       │                           AES-GCM validation
       │                                │
       └───────────────────────┬────────┘
                               ▼
                         Student identity
                               │
                               ▼
                            SQLite
                               │
                 ┌─────────────┼─────────────┐
                 │             │             │
                 ▼             ▼             ▼
             Dashboard      Attendance     Reports
                 │             │             │
                 └─────────────┼─────────────┘
                               ▼
                             WEB UI
                               │
                               ▼
                         USER RESULT

---

# 33. Failure path

    ANY OPERATION
         │
         ▼
      Validate
         │
      ┌──┴─────────┐
      │            │
    VALID        INVALID
      │            │
      ▼            ▼
  Continue       Reject
      │
      ▼
 Hardware / DB / Protocol
      │
   ┌──┴─────────┐
   │            │
 SUCCESS       ERROR
   │            │
   ▼            ▼
Persist       Log error
   │            │
   ▼            ▼
Notify UI   Notify UI
   │            │
   └──────┬─────┘
          ▼
        WEB UI

The architecture repeatedly uses a validate → operate → verify → persist/notify pattern, especially for hardware-backed operations such as fingerprint enrollment and RFID card management.

---

# 34. System boundary

    ┌───────────────────────────────────────────────┐
    │                 DSIS DESKTOP                  │
    │                                               │
    │  HTML / CSS / JavaScript                      │
    │             │                                 │
    │             ▼                                 │
    │          pywebview                            │
    │             │                                 │
    │             ▼                                 │
    │       Python API bridge                       │
    │             │                                 │
    │             ▼                                 │
    │        Python core                            │
    │             │                                 │
    │       ┌─────┴──────────┐                      │
    │       ▼                ▼                      │
    │   SQLite DB       Local filesystem             │
    │                                               │
    └──────────────────┬────────────────────────────┘
                       │
                  USB Serial
                       │
                       ▼
    ┌───────────────────────────────────────────────┐
    │                    ESP32                      │
    │                                               │
    │  Command engine                               │
    │  Fingerprint engine                           │
    │  RFID engine                                  │
    │  LED manager                                  │
    │  JSON / serial protocol                       │
    │                                               │
    └───────────────┬────────────────┬──────────────┘
                    │                │
              UART 57600          SPI
                    │                │
                    ▼                ▼
                  AS608            RC522
                    │                │
                    └───────┬────────┘
                            ▼
                       IDENTIFICATION

---

# 35. Why the architecture is modular

    IDENTIFICATION METHOD
            │
      ┌─────┼───────────────────┐
      │     │                   │
      ▼     ▼                   ▼
 Fingerprint RFID             Future ID
      │     │                   │
     AS608  RC522               │
      │     │                   │
      └─────┴──────────────┬────┘
                           ▼
                    Common DSIS event
                           │
                           ▼
                 Shared Python processing
                           │
                           ▼
                         SQLite
                           │
                           ▼
                     Shared reports/UI

The current repository already demonstrates this separation through fingerprint and RFID paths that converge in the attendance layer.

A future identification method could follow the same overall pattern:

    NEW SENSOR / READER
          │
          ▼
   Device-side event
          │
          ▼
   Python event parser
          │
          ▼
 Identity validation
          │
          ▼
 Shared attendance/database flow

This is an extension pattern, not a claim that every future identification method is already implemented.

---

# 36. Final architecture tree

    DSIS
     │
     ├── USER
     │    └── Desktop UI
     │
     ├── SOFTWARE
     │    ├── Web UI
     │    ├── pywebview
     │    ├── API bridge
     │    ├── Core backend
     │    │    ├── Database
     │    │    ├── Serial
     │    │    ├── Device discovery
     │    │    ├── Attendance
     │    │    ├── Calendar/status
     │    │    ├── Authentication
     │    │    ├── Permissions
     │    │    ├── RFID crypto
     │    │    ├── Logging
     │    │    ├── Setup wizard
     │    │    └── Utilities
     │    ├── Services
     │    ├── Reports
     │    ├── Backup/restore
     │    └── Settings
     │
     ├── HARDWARE
     │    ├── ESP32
     │    ├── AS608
     │    └── RC522
     │
     ├── IDENTIFICATION
     │    ├── Fingerprint
     │    │    └── AS608
     │    └── RFID
     │         ├── CardDetector
     │         ├── ClassicAdapter
     │         └── Type2Adapter
     │
     ├── PERSISTENCE
     │    ├── SQLite
     │    ├── settings.json
     │    ├── backups
     │    ├── logs
     │    ├── exports
     │    └── charts
     │
     ├── QUALITY
     │    ├── Unit tests
     │    ├── Integration tests
     │    ├── GUI smoke tests
     │    └── Hardware/firmware tests
     │
     ├── TOOLING
     │    ├── Database tools
     │    ├── Serial tools
     │    ├── Runtime tools
     │    └── Diagnostics
     │
     ├── DOCUMENTATION
     │    ├── Architecture
     │    ├── Hardware
     │    ├── User Guide
     │    ├── Development
     │    ├── Troubleshooting
     │    ├── Security
     │    ├── API
     │    └── History
     │
     └── HISTORY
          ├── V1
          ├── V2
          └── V3

---

## Architectural summary

DSIS is not a single fingerprint-attendance script.

It is a layered desktop identification platform in which:

    Physical identification
            ↓
      ESP32 device layer
            ↓
      Serial protocol
            ↓
      Python processing
            ↓
    Validation / identity
            ↓
        SQLite
            ↓
     Reports / statistics
            ↓
          Web UI
            ↓
          Operator

Fingerprint and RFID are sibling identification paths. They share the attendance, persistence, security, reporting, and UI infrastructure instead of duplicating the whole application stack.

That separation is the main reason the current DSIS design can grow without rebuilding the entire system around every new reader or identification method.

---

## Related architecture documents

- [v3 System Architecture](v3-system-architecture.md)
- [Runtime Contract](runtime-contract.md)
- [Software Flow](software-flow.md)
- [Database Schema](database-schema.md)
- [Data and Settings](data-and-settings.md)
- [pywebview Bridge](pywebview-bridge.md)

For the repository-wide documentation map, see [docs/INDEX.md](../INDEX.md).

---

## Generated architecture cross-checks

- The box-and-branch view is [DSIS Project Architecture — Visual Family Tree](../generated/PROJECT_ARCHITECTURE_VISUAL_TREE.md).
- The exact path/function inventory is [Full Project Architecture Tree & Symbol Map](../generated/PROJECT_ARCHITECTURE_TREE.md).
- The generated tree is cross-checked against the current Git tree and `audit/source_line_counts.csv`.
- Verified project snapshot used for the rebuild: `c2eb4d3` with 884 tracked tree paths (783 files/blobs + 101 directories).
- Current source audit: 305 source files and 51,143 physical lines (24,050 code, 19,132 comments, 7,961 blank).