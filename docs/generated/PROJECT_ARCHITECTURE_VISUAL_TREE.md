# DSIS Project Architecture — Visual Family Tree

> The authoritative **box-and-branch architecture diagram** for DSIS.
>
> **Lineage start:** `f0b0074` — the requested architecture-document baseline.
> **Verified project tree snapshot:** `c2eb4d3` (the project state immediately before this repair pass).
> **Source audit:** 305 source files / 51,143 physical lines.
>
> The diagram describes subsystem relationships and data/control flow; it is not a claim that every file is on the same runtime call path.
```text
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                         DIGITAL STUDENT IDENTIFICATION SYSTEM                                │
│                                          DSIS                                               │
└───────────────────────────────────────┬─────────────────────────────────────────────────────┘
                                        │
          ┌─────────────────────────────┼─────────────────────────────┐
          │                             │                             │
          ▼                             ▼                             ▼
┌──────────────────────┐     ┌────────────────────────┐     ┌──────────────────────────────┐
│ 01. DESKTOP APP      │     │ 02. HARDWARE SYSTEM    │     │ 03. PROJECT / SUPPORT       │
└──────────┬───────────┘     └────────────┬───────────┘     └──────────────┬───────────────┘
           │                              │                                │
           │                              │                                ├── Documentation
           │                              │                                ├── Tests
           │                              │                                ├── Build
           │                              │                                ├── Tools
           │                              │                                ├── Audit
           │                              │                                └── Archive
           │                              │
           ▼                              ▼

═══════════════════════════════════════════════════════════════════════════════════════════════
01. DESKTOP APPLICATION
═══════════════════════════════════════════════════════════════════════════════════════════════

┌──────────────────────────────────────────┐
│ ENTRY / LAUNCH                           │
├──────────────────────────────────────────┤
│ run_web_gui.py                           │
│ run_web_gui.bat                          │
└──────────────────────┬───────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────┐
│ python/gui_web/main_web.py               │
├──────────────────────────────────────────┤
│ main()                                   │
│ _logo_path()                             │
│ _handle_uncaught_exception()             │
│                                          │
│ Creates native pywebview window          │
│ Creates Api()                             │
│ Starts background runtime                │
│ Attaches JavaScript bridge               │
│ Handles shutdown                         │
└──────────────────────┬───────────────────┘
                       │
                       ▼
               ┌─────────────────┐
               │    PYWEBVIEW    │
               │   NATIVE WINDOW │
               └────────┬────────┘
                        │
                        ▼
┌──────────────────────────────────────────┐
│ WEB UI                                   │
├──────────────────────────────────────────┤
│ python/gui_web/web/index.html            │
│ python/gui_web/web/app.js                │
│ python/gui_web/web/styles.css            │
└──────────────────────┬───────────────────┘
                       │
       ┌───────────────┼───────────────────────────────────────────┐
       │               │                                           │
       ▼               ▼                                           ▼
┌──────────────┐ ┌──────────────┐                          ┌─────────────────┐
│ UI PAGES     │ │ UI MODALS    │                          │ UI STATE        │
├──────────────┤ ├──────────────┤                          ├─────────────────┤
│ Dashboard    │ │ Enrollment   │                          │ Current page    │
│ Attendance   │ │ Authentication│                         │ Current role    │
│ Students     │ │ Password     │                          │ Device state    │
│ Reports      │ │ RFID         │                          │ Scan state      │
│ Logs         │ │ Calendar     │                          │ Modal state     │
│ Settings     │ │ Wipe/Delete  │                          │ Connection info │
│ Calendar     │ └──────────────┘                          └─────────────────┘
└──────┬───────┘
       │
       ▼
window.pywebview.api
       │
       ▼

═══════════════════════════════════════════════════════════════════════════════════════════════
02. API / BRIDGE
═══════════════════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ python/gui_web/api.py                                                                       │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│ API INTEGRATION BOUNDARY                                                                     │
│                                                                                             │
│ ┌───────────────────────────┐  ┌───────────────────────────┐  ┌───────────────────────────┐ │
│ │ CONNECTION                │  │ STUDENT / ENROLLMENT      │  │ RFID MANAGEMENT           │ │
│ ├───────────────────────────┤  ├───────────────────────────┤  ├───────────────────────────┤ │
│ │ connect()                 │  │ start_enroll()            │  │ start_rfid_register_...() │ │
│ │ disconnect()              │  │ cancel_enroll()           │  │ stop_rfid_register_...()  │ │
│ │ list_ports()              │  │ discard_enrollment()      │  │ start_batch_rfid_erase()  │ │
│ │ list_ports_detailed()     │  │ save_student()            │  │ stop_batch_rfid_erase()   │ │
│ │ get_connection_status()   │  │ delete_student()           │  │ bind_student_card()       │ │
│ │ request_fingerprint_count │  │ delete_on_device()        │  │ clear_student_card()      │ │
│ │ forget_saved_port()       │  │ validate_student_fields() │  │                          │ │
│ └───────────────────────────┘  └───────────────────────────┘  └───────────────────────────┘ │
│                                                                                             │
│ ┌───────────────────────────┐  ┌───────────────────────────┐  ┌───────────────────────────┐ │
│ │ ATTENDANCE / READS        │  │ REPORTS / CALENDAR        │  │ DATA / BACKUP              │ │
│ ├───────────────────────────┤  ├───────────────────────────┤  ├───────────────────────────┤ │
│ │ get_dashboard_stats()     │  │ get_attendance_evaluation │  │ list_backups()            │ │
│ │ get_recent_activity()     │  │ export_attendance_...()   │  │ create_backup()           │ │
│ │ get_attendance()          │  │ get_calendar_month()      │  │ restore_backup()          │ │
│ │ get_students()            │  │ set_calendar_entry()      │  │ wipe_all_data()           │ │
│ │ get_student()             │  │ remove_calendar_entry()   │  │ get_settings()            │ │
│ │ export_attendance_csv()   │  │ get_statistics_report()   │  │ save_ui_settings()        │ │
│ │ export_students_csv()     │  │ export_statistics_report()│  │ restore_default_settings()│ │
│ └───────────────────────────┘  └───────────────────────────┘  └───────────────────────────┘ │
│                                                                                             │
│ ┌───────────────────────────┐  ┌───────────────────────────┐  ┌───────────────────────────┐ │
│ │ AUTH / PERMISSIONS        │  │ SETUP                     │  │ UI EVENTS / LIFECYCLE      │ │
│ ├───────────────────────────┤  ├───────────────────────────┤  ├───────────────────────────┤ │
│ │ authenticate_role()       │  │ is_first_run_setup...()   │  │ scan_result               │ │
│ │ get_current_role()        │  │ complete_first_run_...()  │  │ serial_line               │ │
│ │ set_current_role()        │  │ get_setup_wizard_step()   │  │ log_line                  │ │
│ │ get_session_state()       │  │ complete_setup_device...  │  │ enroll_progress           │ │
│ │ touch_session()           │  │ complete_setup_schedule.. │  │ delete_progress           │ │
│ │ lock_session()            │  │ complete_setup_branding.. │  │ wipe_progress             │ │
│ │ change_admin_password()   │  └───────────────────────────┘  │ fingerprint_count          │ │
│ │ get_role_permissions()    │                                 │ connection_status         │ │
│ └───────────────────────────┘                                 │ data_changed              │ │
│                                                               │ mode_changed              │ │
│                                                               └───────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
                               ┌────────────────────┐
                               │  PYTHON CORE       │
                               └─────────┬──────────┘
                                         │

═══════════════════════════════════════════════════════════════════════════════════════════════
03. CORE BACKEND FAMILY
═══════════════════════════════════════════════════════════════════════════════════════════════

                    ┌─────────────────────────────────────────────┐
                    │              python/core/                   │
                    └──────────────────────┬──────────────────────┘
                                           │
      ┌────────────────┬───────────────────┼───────────────────┬────────────────┐
      │                │                   │                   │                │
      ▼                ▼                   ▼                   ▼                ▼
┌────────────┐  ┌────────────┐      ┌────────────┐      ┌────────────┐   ┌────────────┐
│ database   │  │ serial_    │      │ device_    │      │ commands   │   │ attendance │
│ .py        │  │ handler.py │      │ discovery  │      │ .py        │   │ .py        │
└─────┬──────┘  └─────┬──────┘      │ .py        │      └─────┬──────┘   └─────┬──────┘
      │                │             └─────┬──────┘            │                  │
      │                │                   │                   │                  │
      │                │                   │                   │                  │
      ▼                ▼                   ▼                   ▼                  ▼
┌────────────┐  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌────────────────┐
│ SQLite DB  │  │ Serial I/O   │   │ Port ranking │   │ ESP32 cmd    │   │ Attendance     │
│            │  │ Reader       │   │ ID? probe    │   │ wrappers     │   │ Processor      │
├────────────┤  ├──────────────┤   ├──────────────┤   ├──────────────┤   ├────────────────┤
│ init_db    │  │ connect()    │   │ list_ports() │   │ cmd_scan()   │   │ process_line() │
│ migrations │  │ disconnect() │   │ score ports  │   │ cmd_stop()   │   │ fingerprint    │
│ students   │  │ send_command │   │ probe port   │   │ cmd_enroll() │   │ RFID events    │
│ attendance │  │ read_line()  │   │ handshake    │   │ cmd_delete() │   │ confidence     │
│ reports    │  │ reconnect    │   │ validate     │   │ cmd_wipe()   │   │ cooldown       │
│ backups    │  │ read thread  │   │ adopt device │   │ cmd_list()   │   │ persistence    │
│ restore    │  │ connection   │   └──────────────┘   │ card write   │   └────────────────┘
└────────────┘  └──────────────┘                      │ card erase   │
                                                     └──────────────┘
      │                │                   │                   │                  │
      └────────────────┴───────────────────┴───────────────────┴──────────────────┘
                                           │
      ┌────────────────┬──────────────────┼───────────────────┬────────────────┐
      │                │                  │                   │                │
      ▼                ▼                  ▼                   ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ attendance_  │ │ attendance_  │ │ auth.py      │ │ permissions  │ │ rfid_card.py │
│ status.py    │ │ calendar.py  │ │              │ │ .py          │ │              │
├──────────────┤ ├──────────────┤ ├──────────────┤ ├──────────────┤ ├──────────────┤
│ _minutes()   │ │ date rules   │ │ hash_password│ │ set_role()    │ │ key creation │
│ calculate_   │ │ holidays     │ │ verify_pass  │ │ touch_session│ │ UID normalize│
│ attendance_  │ │ suspensions  │ │ PBKDF2       │ │ has_permission│ │ encrypt     │
│ status()     │ │ half-days    │ │ first-run    │ │ require_perm │ │ decrypt     │
│              │ │ weekdays     │ │ auth state   │ │ role hierarchy│ │ AES-GCM     │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
      │                │                  │                │                │
      └────────────────┴──────────────────┼────────────────┴────────────────┘
                                          │
                   ┌──────────────────────┼──────────────────────┐
                   │                      │                      │
                   ▼                      ▼                      ▼
             logger.py               setup_wizard.py          utils.py
                   │                      │                      │
             ┌─────┴─────┐          ┌─────┴────────┐       ┌─────┴────────┐
             │           │          │              │       │              │
             ▼           ▼          ▼              ▼       ▼              ▼
          Console      File      Password       Device   JSON-line      shared
          logs         logs      step           step     parsing        helpers
                                  │              │
                                  ▼              ▼
                                Schedule       Branding
                                  step           step

═══════════════════════════════════════════════════════════════════════════════════════════════
04. SERVICE FAMILY
═══════════════════════════════════════════════════════════════════════════════════════════════

                         python/services/
                                │
                     ┌──────────┴──────────┐
                     │                     │
                     ▼                     ▼
          ┌────────────────────┐  ┌────────────────────┐
          │ student_service.py │  │ attendance_service │
          ├────────────────────┤  ├────────────────────┤
          │ get_all_students() │  │ get_today()        │
          │ get_student()      │  │ get_paginated()    │
          │ save_student()     │  │ log()              │
          │ delete_student()  │  │                    │
          └──────────┬─────────┘  └──────────┬─────────┘
                     │                       │
                     └──────────────┬────────┘
                                    ▼
                                Core layer

═══════════════════════════════════════════════════════════════════════════════════════════════
05. HARDWARE SYSTEM
═══════════════════════════════════════════════════════════════════════════════════════════════

                         ┌─────────────────────────────┐
                         │       ESP32 WROOM-32        │
                         │       DSIS All-In-One       │
                         └──────────────┬──────────────┘
                                        │
              ┌─────────────────────────┼─────────────────────────┐
              │                         │                         │
              ▼                         ▼                         ▼
       ┌──────────────┐          ┌──────────────┐          ┌──────────────┐
       │ USB SERIAL   │          │ UART 2       │          │ SPI BUS      │
       │ 115200       │          │ 57600        │          │              │
       └──────┬───────┘          └──────┬───────┘          └──────┬───────┘
              │                         │                         │
              ▼                         ▼                         ▼
          Windows PC                 AS608                     RC522
              │                         │                         │
              │                         ▼                         ▼
              │                    Fingerprint                RFID
              │                    enrollment                  reader
              │                    + matching
              ▼

═══════════════════════════════════════════════════════════════════════════════════════════════
06. ESP32 FIRMWARE FAMILY
═══════════════════════════════════════════════════════════════════════════════════════════════

                         firmware/ESP32_DSIS_AllInOne/
                                        │
                                        ▼
                         ESP32_DSIS_AllInOne.ino
                                        │
             ┌──────────────────────────┼──────────────────────────┐
             │                          │                          │
             ▼                          ▼                          ▼
      ┌──────────────┐          ┌──────────────┐          ┌─────────────────┐
      │ HOST         │          │ FINGERPRINT  │          │ RFID ENGINE     │
      │ INTERFACE    │          │ ENGINE       │          │                 │
      ├──────────────┤          ├──────────────┤          ├─────────────────┤
      │ ID?          │          │ getImage()   │          │ detect card     │
      │ SCAN         │          │ image2Tz()   │          │ read UID        │
      │ STOP         │          │ fingerSearch │          │ detect family   │
      │ ENROLL       │          │ createModel  │          │ adapter select  │
      │ ENROLL:<id>  │          │ storeModel   │          │ read payload    │
      │ DELETE:<id>  │          │ loadModel    │          │ write payload   │
      │ WIPE         │          │ deleteModel  │          │ verify readback │
      │ LIST         │          │ emptyDatabase│          └────────┬────────┘
      │ STATUS:<...> │          │ getTemplate  │                   │
      │ CARD_WRITE   │          └──────────────┘         ┌─────────┴─────────┐
      │ CARD_ERASE   │                                   │                   │
      └──────┬───────┘                                   ▼                   ▼
             │                                   ┌──────────────┐    ┌──────────────┐
             ▼                                   │ ClassicAdapter│    │ Type2Adapter │
     Structured JSON                             ├──────────────┤    ├──────────────┤
     + text events                               │ authenticate │    │ read pages   │
                                                 │ read blocks  │    │ write pages  │
                                                 │ write blocks │    │ verify       │
                                                 │ verify       │    └──────────────┘
                                                 └──────┬───────┘
                                                        │
                                                        ▼
                                                  48-byte payload

═══════════════════════════════════════════════════════════════════════════════════════════════
07. FINGERPRINT FAMILY
═══════════════════════════════════════════════════════════════════════════════════════════════

                              ┌──────────┐
                              │  AS608   │
                              └────┬─────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
             ┌──────────────┐             ┌──────────────┐
             │ ENROLLMENT   │             │ ATTENDANCE   │
             └──────┬───────┘             └──────┬───────┘
                    │                              │
                    ▼                              ▼
             Find free ID                      Place finger
                    │                              │
                    ▼                              ▼
             First capture                   getImage()
                    │                              │
                    ▼                              ▼
               image2Tz(1)                    image2Tz()
                    │                              │
                    ▼                              ▼
              Remove finger                  Search model
                    │                              │
                    ▼                       ┌──────┴──────┐
             Second capture                 │             │
                    │                      MATCH       NO MATCH
                    ▼                        │             │
               image2Tz(2)                   ▼             ▼
                    │                    confidence     UNKNOWN
                    ▼
              createModel()
                    │
              ┌─────┴─────┐
              │           │
              ▼           ▼
          SUCCESS       FAILURE
              │           │
              ▼           ▼
         storeModel()    error
              │
              ▼
       enrollment event
              │
              ▼
       Python save_student()
              │
              ▼
            SQLite

Fingerprint IDs:
    ├── 0       → Unregistered / Unknown placeholder
    └── 1–127   → AS608 fingerprint templates

═══════════════════════════════════════════════════════════════════════════════════════════════
08. RFID FAMILY
═══════════════════════════════════════════════════════════════════════════════════════════════

                              ┌──────────┐
                              │  RC522   │
                              └────┬─────┘
                                   │
                                   ▼
                           Detect card + UID
                                   │
                                   ▼
                         ┌───────────────────┐
                         │   CardDetector    │
                         └─────────┬─────────┘
                                   │
              ┌────────────────────┼───────────────────────────────┐
              │                    │                               │
              ▼                    ▼                               ▼
       ┌──────────────┐     ┌──────────────┐               ┌──────────────┐
       │ CLASSIC      │     │ TYPE 2       │               │ OTHER        │
       ├──────────────┤     ├──────────────┤               ├──────────────┤
       │ MIFARE Mini  │     │ Ultralight   │               │ MIFARE Plus  │
       │ MIFARE 1K    │     │ NTAG215      │               │ DESFire      │
       │ MIFARE 4K    │     │ NTAG216      │               │ ISO14443-4   │
       └──────┬───────┘     └──────┬───────┘               │ ambiguous    │
              │                    │                       │ unknown      │
              ▼                    ▼                       └──────┬───────┘
       ┌──────────────┐     ┌──────────────┐                      │
       │ ClassicAdapter│    │ Type2Adapter │                      ▼
       ├──────────────┤     ├──────────────┤                 unsupported /
       │ authenticate │     │ read pages   │                 unreadable
       │ read blocks  │     │ write pages  │
       │ write blocks │     │ verify       │
       │ verify       │     └──────┬───────┘
       └──────┬───────┘            │
              │                    │
              └─────────┬──────────┘
                        ▼
                 48-byte DSIS payload
                        │
                        ▼
                  Python RFID layer

CardDetector files:
    ├── CardDetector.h
    └── CardDetector.cpp

Classic adapter files:
    ├── ClassicAdapter.h
    └── ClassicAdapter.cpp

Type 2 adapter files:
    ├── Type2Adapter.h
    └── Type2Adapter.cpp

═══════════════════════════════════════════════════════════════════════════════════════════════
09. RFID CRYPTOGRAPHIC FAMILY
═══════════════════════════════════════════════════════════════════════════════════════════════

                         python/core/rfid_card.py
                                  │
              ┌───────────────────┼────────────────────┐
              │                   │                    │
              ▼                   ▼                    ▼
       Application key        UID normalize       Payload format
              │                   │                    │
              ▼                   ▼                    ▼
          AES-256             normalized UID     version + nonce
                                                   + ciphertext/tag
                                                        │
                                                        ▼
                                              encrypted plaintext
                                                        │
                                    ┌───────────────────┴───────────────────┐
                                    │                                       │
                                    ▼                                       ▼
                            Fingerprint ID                         Student number
                                    │                                       │
                                    └───────────────────┬───────────────────┘
                                                        ▼
                                                UID-bound AAD
                                                        │
                                                        ▼
                                                AES-GCM verify
                                                        │
                                              ┌─────────┴─────────┐
                                              │                   │
                                            VALID               INVALID
                                              │                   │
                                              ▼                   ▼
                                         identity            UNKNOWN / reject

═══════════════════════════════════════════════════════════════════════════════════════════════
10. RFID ATTENDANCE FAMILY
═══════════════════════════════════════════════════════════════════════════════════════════════

RC522
  │
  ▼
Detect card
  │
  ▼
Read UID
  │
  ▼
CardDetector
  │
  ├────────────── Supported ────────────────┐
  │                                         │
  │                                         ▼
  │                                      Adapter
  │                                         │
  │                                         ▼
  │                                  Read 48B payload
  │                                         │
  │                                         ▼
  │                                    JSON event
  │                                         │
  │                                         ▼
  └──────────────────────────────────► SerialHandler
                                            │
                                            ▼
                                      AttendanceProcessor
                                            │
                                 ┌──────────┴──────────┐
                                 │                     │
                                 ▼                     ▼
                            Normalize UID        AES-GCM decrypt
                                                       │
                                                       ▼
                                                 identity payload
                                                       │
                                    ┌──────────────────┴───────────────────┐
                                    │                                      │
                                    ▼                                      ▼
                              fingerprint_id                        student_no
                                    │                                      │
                                    └──────────────────┬───────────────────┘
                                                       ▼
                                               student database lookup
                                                       │
                                      ┌────────────────┼────────────────┐
                                      │                │                │
                                      ▼                ▼                ▼
                                  student ID      student number     card UID
                                  agreement          agreement        agreement
                                      │                │                │
                                      └────────────────┼────────────────┘
                                                       ▼
                                                identity accepted
                                                       │
                                                       ▼
                                                cooldown check
                                                       │
                                             ┌─────────┴─────────┐
                                             │                   │
                                           BLOCKED             ALLOWED
                                             │                   │
                                             ▼                   ▼
                                         duplicate             log
                                                                   │
                                                                   ▼
                                                                 SQLite

═══════════════════════════════════════════════════════════════════════════════════════════════
11. RFID REGISTRATION FAMILY
═══════════════════════════════════════════════════════════════════════════════════════════════

Student selected
      │
      ▼
start_rfid_register_session()
      │
      ├── permission check
      ├── student exists
      └── session conflict check
      │
      ▼
Start card mode
      │
      ▼
Tap card
      │
      ▼
Read UID + detect family
      │
      ▼
Check current owner
      │
    ┌─┴───────────────┐
    │                 │
  linked           available
    │                 │
    ▼                 ▼
  reject          encrypt payload
                      │
                      ▼
                  CARD_WRITE_HEX
                      │
                      ▼
                    ESP32
                      │
          ┌───────────┴───────────┐
          │                       │
          ▼                       ▼
      ClassicAdapter          Type2Adapter
          │                       │
          └───────────┬───────────┘
                      ▼
                 Write + readback
                      │
                      ▼
               write_verified
                      │
          ┌───────────┼───────────┐
          │           │           │
          ▼           ▼           ▼
        UID        payload      verified
        match      match         flag
          │           │           │
          └───────────┴───────────┘
                      │
                      ▼
              bind_student_card()
                      │
                      ▼
                 SQLite link

═══════════════════════════════════════════════════════════════════════════════════════════════
12. ENROLLMENT FAMILY
═══════════════════════════════════════════════════════════════════════════════════════════════

Student form
    │
    ▼
validate_student_fields()
    │
    ▼
start_enroll()
    │
    ├── permission
    ├── mode conflict
    └── stop active scan
    │
    ▼
ENROLL
    │
    ▼
ESP32
    │
    ▼
AS608
    │
    ├── capture #1
    ├── template slot 1
    ├── wait for removal
    ├── capture #2
    ├── template slot 2
    ├── create model
    └── store model
    │
    ▼
Enrollment success
    │
    ▼
Python receives fingerprint ID
    │
    ▼
save_student()
    │
    ▼
students table

═══════════════════════════════════════════════════════════════════════════════════════════════
13. ATTENDANCE FAMILY
═══════════════════════════════════════════════════════════════════════════════════════════════

                    IDENTIFICATION
                          │
               ┌──────────┴──────────┐
               │                     │
               ▼                     ▼
         Fingerprint                 RFID
               │                     │
               ▼                     ▼
             AS608                  RC522
               │                     │
               └──────────┬──────────┘
                          ▼
                  AttendanceProcessor
                          │
                 ┌────────┴─────────┐
                 │                  │
             Known identity      Unknown
                 │                  │
                 ▼                  ▼
          Confidence / UID       ID 0
                 │                  │
                 ▼                  ▼
             Cooldown           UNKNOWN record
                 │
        ┌────────┴────────┐
        │                 │
      duplicate          allowed
        │                 │
        ▼                 ▼
      ignore           log attendance
                              │
                         ┌────┴────┐
                         │         │
                       time_in   time_out
                         │         │
                         └────┬────┘
                              ▼
                         attendance.db

═══════════════════════════════════════════════════════════════════════════════════════════════
14. DATABASE FAMILY
═══════════════════════════════════════════════════════════════════════════════════════════════

                         python/core/database.py
                                  │
                     ┌────────────┴─────────────┐
                     │                          │
                     ▼                          ▼
               students table            attendance table
                     │                          │
          ┌──────────┼──────────┐               │
          │          │          │               │
          ▼          ▼          ▼               ▼
 fingerprint_id  student_no  card_uid       attendance ID
 student_name    grade       enrollment     fingerprint_id
 section         updated     updated         date / time
                                           confidence
                                           status
                                           timestamp
                                           event_type
                     │                          │
                     └────────────┬─────────────┘
                                  ▼
                           Foreign-key link
                                  │
                                  ▼
                           historical records

ID 0
 │
 └── Unregistered / Unknown
       │
       └── durable placeholder for retained unknown history

DATABASE FUNCTIONS
 │
 ├── init_database()
 ├── schema creation / migration
 ├── student CRUD
 ├── card binding / clearing
 ├── attendance logging
 ├── attendance queries
 ├── statistics
 ├── report generation
 ├── CSV preparation
 ├── chart generation
 ├── backup_database()
 ├── restore_database()
 └── list_backups()

═══════════════════════════════════════════════════════════════════════════════════════════════
15. AUTHENTICATION + PERMISSION FAMILY
═══════════════════════════════════════════════════════════════════════════════════════════════

                           FIRST RUN
                              │
                              ▼
                      Create admin password
                              │
                              ▼
                       hash_password()
                              │
                              ▼
                    PBKDF2-HMAC-SHA256
                              │
                              ▼
                         settings.json
                              │
                              ▼
                         authenticate
                              │
                ┌─────────────┼─────────────┐
                │             │             │
                ▼             ▼             ▼
              GUEST         TEACHER        ADMIN
                │             │             │
                └─────────────┼─────────────┘
                              ▼
                     permissions.py
                              │
                 ┌────────────┴─────────────┐
                 │                          │
                 ▼                          ▼
               ALLOW                      DENY
                 │                          │
                 ▼                          ▼
             operation                   safe error
                 │
                 ▼
              session
                 │
                 ▼
            idle timeout
                 │
                 ▼
               guest

═══════════════════════════════════════════════════════════════════════════════════════════════
16. SETTINGS + SETUP FAMILY
═══════════════════════════════════════════════════════════════════════════════════════════════

                           settings_store.py
                                  │
                                  ▼
                         data/settings.json
                                  │
       ┌──────────────────────────┼──────────────────────────────┐
       │                          │                              │
       ▼                          ▼                              ▼
   CONNECTION                 ATTENDANCE                        UI
       │                          │                              │
       ├── COM port               ├── cooldown                   ├── theme
       ├── baud                   ├── min_confidence             ├── branding
       ├── auto detect            ├── time in/out                └── display state
       └── auto reconnect         ├── early
                                  ├── late
                                  └── absent
       │
       ├─────────────────────┬──────────────────┐
       ▼                     ▼                  ▼
    CALENDAR               BACKUP           SETUP STATE
       │                     │                  │
       ├── holidays          └── interval      ├── device
       ├── suspensions                          ├── schedule
       ├── half-days                            └── branding
       └── weekdays
                                  │
                                  ▼
                              AUTH DATA

═══════════════════════════════════════════════════════════════════════════════════════════════
17. REPORTING FAMILY
═══════════════════════════════════════════════════════════════════════════════════════════════

                         attendance.db
                              │
                              ▼
                      Reporting functions
                              │
             ┌────────────────┼──────────────────┐
             │                │                  │
             ▼                ▼                  ▼
          Attendance       Statistics        Evaluation
             │                │                  │
             ├── day          ├── totals         ├── day
             ├── week         ├── grade          ├── week
             └── month        ├── section        └── month
                              └── timeline
             │                │                  │
             └────────────────┼──────────────────┘
                              ▼
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
                   CSV               Charts
                    │                   │
                    └─────────┬─────────┘
                              ▼
                         Export files

═══════════════════════════════════════════════════════════════════════════════════════════════
18. RUNTIME / THREAD FAMILY
═══════════════════════════════════════════════════════════════════════════════════════════════

                            DSIS PROCESS
                                │
          ┌─────────────────────┼──────────────────────────┐
          │                     │                          │
          ▼                     ▼                          ▼
       Main UI             Serial Reader             Background
          │                     │                     workers
          │                     │                          │
          │                     ├── read lines             ├── auto backup
          │                     ├── buffer                └── auto reconnect
          │                     ├── parse JSON
          │                     └── feed processor
          │                              │
          ▼                              ▼
      pywebview                  AttendanceProcessor
          │                              │
          ▼                              ▼
       app.js                     SQLite / events

═══════════════════════════════════════════════════════════════════════════════════════════════
19. LOGGING FAMILY
═══════════════════════════════════════════════════════════════════════════════════════════════

                           core/logger.py
                                │
                 ┌──────────────┼───────────────┐
                 │              │               │
                 ▼              ▼               ▼
              Console          File          UI buffer
                 │              │               │
                 │              ▼               ▼
                 │          data/logs/       log_line
                 │
          ┌──────┴──────────────────────────────────┐
          │                                         │
       structured                                diagnostics
       logging                                     │
          │                                         ├── startup
          ├── startup                               ├── device
          ├── device                                ├── serial
          ├── serial                                ├── attendance
          ├── attendance                            ├── security
          ├── security                              └── errors
          └── errors

═══════════════════════════════════════════════════════════════════════════════════════════════
20. FIRMWARE TEST / VARIANT FAMILY
═══════════════════════════════════════════════════════════════════════════════════════════════

firmware/
   │
   ├── ACTIVE
   │    └── ESP32_DSIS_AllInOne/
   │         ├── ESP32_DSIS_AllInOne.ino
   │         └── src/rfid/
   │              ├── CardDetector.*
   │              ├── ClassicAdapter.*
   │              └── Type2Adapter.*
   │
   ├── EARLIER
   │    └── ESP32_Fingerprint_AllInOne/
   │
   └── TEST SKETCHES
        ├── attendance
        ├── enroll
        ├── delete
        ├── rc522_test
        ├── rc522_read
        ├── rc522_write
        ├── rc522_readwrite
        ├── rc522_dumpinfo_test
        └── fingerprint_check

═══════════════════════════════════════════════════════════════════════════════════════════════
21. TESTING FAMILY
═══════════════════════════════════════════════════════════════════════════════════════════════

tests/
   │
   ├── UNIT
   │    ├── attendance parsing
   │    ├── attendance processor
   │    ├── attendance status
   │    ├── attendance export
   │    ├── database
   │    ├── database security
   │    ├── authentication
   │    ├── permissions
   │    ├── settings
   │    ├── RFID
   │    └── validation
   │
   ├── GUI / WEB
   │    ├── web smoke
   │    ├── settings integration
   │    ├── shutdown
   │    ├── responsive layout
   │    ├── enrollment dialog
   │    └── UI regressions
   │
   ├── SERIAL / DEVICE
   │    ├── active firmware protocol
   │    ├── auto port probe
   │    ├── host gate
   │    ├── troubleshooting
   │    ├── boot banner
   │    └── sensor recovery
   │
   ├── HARDWARE
   │    └── physical_esp32_smoke.py
   │
   └── PROTOTYPES
        ├── Qt prototypes
        ├── hybrid prototypes
        ├── original UI
        ├── task-manager variant
        └── prototype test suites

═══════════════════════════════════════════════════════════════════════════════════════════════
22. BUILD FAMILY
═══════════════════════════════════════════════════════════════════════════════════════════════

Build/
   │
   ├── DSIS_v1.spec
   ├── DSIS_v2.spec
   └── DSIS_v3.spec
            │
            ▼
        PyInstaller
            │
            ▼
     Windows distribution

tools/
   └── fingerprint_portable.spec
            │
            ▼
       portable build

═══════════════════════════════════════════════════════════════════════════════════════════════
23. DEVELOPMENT TOOLS FAMILY
═══════════════════════════════════════════════════════════════════════════════════════════════

tools/
   │
   ├── _database_refactor.py
   ├── archive_unused_python.py
   ├── copilot_forensic_search.py
   ├── debug_db_connections.py
   ├── list_files.bat
   ├── runtime_manager.py
   ├── serial_handler_connect_probe.py
   ├── serial_pipeline_tester.py
   ├── serial_worker_probe.py
   └── verify_gui_startup.py
            │
            ├── database diagnostics
            ├── serial diagnostics
            ├── runtime inspection
            ├── forensic investigation
            └── startup verification

═══════════════════════════════════════════════════════════════════════════════════════════════
24. DOCUMENTATION FAMILY
═══════════════════════════════════════════════════════════════════════════════════════════════

docs/
   │
   ├── Architecture
   │    ├── complete-system-architecture.md
   │    ├── PROJECT ARCHITECTURE VISUAL TREE  ← this diagram
   │    ├── v3-system-architecture.md
   │    ├── v3-system-architecture-detail.md
   │    ├── runtime-contract.md
   │    ├── software-flow.md
   │    ├── database-schema.md
   │    ├── pywebview-bridge.md
   │    └── pywebview-bridge-api-reference.md
   │
   ├── Hardware
   │    ├── wiring
   │    ├── hardware connections
   │    ├── firmware
   │    ├── serial protocol
   │    ├── drivers / ports
   │    └── firmware variants
   │
   ├── User Guide
   │    ├── installation
   │    ├── workflows
   │    ├── enrollment / scanning
   │    ├── attendance rules
   │    ├── roles / permissions
   │    ├── first-run wizard
   │    └── backup / restore / export
   │
   ├── Development
   │    ├── setup
   │    ├── testing
   │    ├── logging
   │    ├── runtime data
   │    ├── release / build
   │    ├── changelog
   │    └── documentation authority
   │
   ├── Troubleshooting
   ├── Security
   ├── API
   ├── History
   ├── Overview
   ├── Research
   ├── Dup / investigations
   └── generated reference material

═══════════════════════════════════════════════════════════════════════════════════════════════
25. ARCHIVE / VERSION FAMILY
═══════════════════════════════════════════════════════════════════════════════════════════════

                                  DSIS HISTORY
                                       │
                   ┌───────────────────┼───────────────────┐
                   │                   │                   │
                   ▼                   ▼                   ▼
                  V1                  V2                  V3
                   │                   │                   │
             CustomTkinter         PySide6 / Qt       HTML + JS
                   │                   │                   │
                   │                   │                pywebview
                   │                   │                   │
                   ▼                   ▼                   ▼
              legacy GUI         Qt GUI / workers    current runtime
                   │                   │                   │
                   └───────────────────┼───────────────────┘
                                       │
                                       ▼
                              shared evolution
                                       │
                 ┌─────────────────────┼─────────────────────┐
                 │                     │                     │
                 ▼                     ▼                     ▼
              Serial                Database             Attendance
                 │                     │                     │
                 └─────────────────────┼─────────────────────┘
                                       ▼
                                  Current DSIS

archive/
   │
   ├── diagnostics
   ├── legacy-ui/gui_qt_redesign
   ├── legacy-ui/gui_qt_redesign_2
   ├── legacy-ui/testing_area
   ├── legacy-ui/v1
   └── legacy-ui/v2

Archived code is preserved as lineage/reference and is not merged into the current V3 runtime tree.

═══════════════════════════════════════════════════════════════════════════════════════════════
26. COMPLETE IDENTIFICATION PATH
═══════════════════════════════════════════════════════════════════════════════════════════════

                              USER
                               │
                               ▼
                         DSIS DESKTOP UI
                               │
                               ▼
                         pywebview API
                               │
                               ▼
                          Python Api
                               │
                    ┌──────────┴───────────┐
                    │                      │
                    ▼                      ▼
               Fingerprint                RFID
                    │                      │
                    ▼                      ▼
                   AS608                  RC522
                    │                      │
                    └──────────┬───────────┘
                               ▼
                         ESP32 EVENT
                               │
                               ▼
                         SERIAL 115200
                               │
                               ▼
                         SerialHandler
                               │
                               ▼
                      AttendanceProcessor
                               │
                   ┌───────────┴───────────┐
                   │                       │
                   ▼                       ▼
              Validation              Identification
                   │                       │
                   └───────────┬───────────┘
                               ▼
                             SQLite
                               │
                  ┌────────────┼──────────────┐
                  │            │              │
                  ▼            ▼              ▼
             Attendance      Reports      Statistics
                  │            │              │
                  └────────────┼──────────────┘
                               ▼
                              UI
                               │
                               ▼
                             USER

═══════════════════════════════════════════════════════════════════════════════════════════════
27. COMPLETE DATA / CONTROL TREE
═══════════════════════════════════════════════════════════════════════════════════════════════

DSIS
 │
 ├── PRESENTATION
 │    ├── HTML
 │    ├── JavaScript
 │    ├── CSS
 │    └── pywebview
 │
 ├── APPLICATION
 │    ├── Api bridge
 │    ├── Core
 │    ├── Services
 │    └── Runtime workers
 │
 ├── IDENTIFICATION
 │    ├── Fingerprint
 │    │    └── AS608
 │    └── RFID
 │         └── RC522
 │
 ├── DEVICE CONTROL
 │    └── ESP32
 │         ├── command engine
 │         ├── scan engine
 │         ├── fingerprint engine
 │         └── RFID engine
 │
 ├── SECURITY
 │    ├── authentication
 │    ├── permissions
 │    ├── AES-GCM RFID validation
 │    └── UID / identity agreement
 │
 ├── PERSISTENCE
 │    ├── SQLite
 │    ├── settings.json
 │    ├── backups
 │    ├── logs
 │    ├── exports
 │    └── charts
 │
 ├── REPORTING
 │    ├── attendance
 │    ├── evaluation
 │    ├── statistics
 │    └── exports
 │
 ├── QUALITY
 │    ├── unit tests
 │    ├── integration tests
 │    ├── GUI tests
 │    ├── serial tests
 │    └── hardware smoke tests
 │
 ├── BUILD
 │    ├── V1
 │    ├── V2
 │    └── V3
 │
 └── HISTORY
      ├── V1
      ├── V2
      ├── V3
      └── archived experiments

═══════════════════════════════════════════════════════════════════════════════════════════════
FINAL TREE
═══════════════════════════════════════════════════════════════════════════════════════════════

                              ┌──────────────────────┐
                              │        DSIS          │
                              └──────────┬───────────┘
                                         │
         ┌───────────────────────────────┼─────────────────────────────────┐
         │                               │                                 │
         ▼                               ▼                                 ▼
      DESKTOP                         HARDWARE                          SUPPORT
         │                               │                                 │
         ├── Web UI                      ├── ESP32                         ├── Docs
         │   ├── HTML                    │   ├── AS608                     ├── Tests
         │   ├── JS                      │   ├── RC522                     ├── Build
         │   └── CSS                     │   └── LED / protocol             ├── Tools
         │                               │                                 ├── Audit
         ├── pywebview                   └──────────────┬──────────────────┤
         │                                               │
         ├── Api bridge                                  ▼
         │                                         IDENTIFICATION
         │                                               │
         ├── Core                              ┌─────────┴──────────┐
         │   ├── Database                      │                    │
         │   ├── Serial                         ▼                    ▼
         │   ├── Discovery                  Fingerprint           RFID
         │   ├── Attendance                     │                    │
         │   ├── Auth                            ▼                    ▼
         │   ├── Permissions                   AS608                RC522
         │   ├── RFID Crypto                     │                    │
         │   ├── Calendar                        └────────┬───────────┘
         │   ├── Status                                    ▼
         │   ├── Logger                               DEVICE EVENT
         │   ├── Setup                                    │
         │   └── Utils                                    ▼
         │                                           SERIAL PROTOCOL
         ├── Services                                   │
         │   ├── Student                                ▼
         │   └── Attendance                         PYTHON CORE
         │                                               │
         └──────────────────────────────────────┬────────┘
                                                │
                                                ▼
                                             SQLite
                                                │
                              ┌─────────────────┼─────────────────┐
                              │                 │                 │
                              ▼                 ▼                 ▼
                          Attendance         Reports          Statistics
                              │                 │                 │
                              └─────────────────┼─────────────────┘
                                                ▼
                                              WEB UI
                                                │
                                                ▼
                                               USER

```

## Reading rule

This tree describes the **relationship between parts**, not merely where files happen to live.

A file can belong to a subsystem while its functions participate in a different runtime path. The arrows therefore describe architectural responsibility and data/control flow, while the file names identify the implementation locations.

For exact source inventories, use the companion generated project tree and application inventory.
---

## Expanded architecture diagram,,> The following is the full expanded box-and-branch architecture view, preserved as a single diagram so the subsystem relationships can be read top-to-bottom.,,```text,                         ┌──────────────────────────────────────┐
                         │  DIGITAL STUDENT IDENTIFICATION     │
                         │              SYSTEM                 │
                         │               DSIS                   │
                         └──────────────────┬───────────────────┘
                                            │
             ┌──────────────────────────────┼──────────────────────────────┐
             │                              │                              │
             ▼                              ▼                              ▼
     DESKTOP APPLICATION              HARDWARE SYSTEM              PROJECT / SUPPORT
             │                              │                              │
             │                              │                              │
═════════════╪══════════════════════════════╪══════════════════════════════╪═══════
             │                              │                              │
             ▼                              ▼                              ▼


┌──────────────────────────────┐
│      01. DESKTOP APP        │
└──────────────┬───────────────┘
               │
               ├── Launch
               │   │
               │   ├── run_web_gui.py
               │   └── run_web_gui.bat
               │
               ▼
        gui_web.main_web
               │
               ├── Install exception hooks
               ├── Create Api()
               ├── Initialize runtime
               ├── Initialize database
               ├── Initialize logging
               ├── Load settings
               ├── Create pywebview window
               ├── Attach Api bridge
               └── Start native UI loop
               │
               ▼
      ┌───────────────────────┐
      │     PYWEBVIEW         │
      │    NATIVE WINDOW      │
      └───────────┬───────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │     WEB UI          │
        └──────────┬──────────┘
                   │
      ┌────────────┼───────────────────────────────────────┐
      │            │                  │                    │
      ▼            ▼                  ▼                    ▼
 index.html      app.js           styles.css          UI STATE
      │            │                  │                    │
      │            ├── Dashboard      │                    ├── Current page
      │            ├── Attendance     │                    ├── Current role
      │            ├── Students       │                    ├── Device state
      │            ├── Reports        │                    ├── Scan state
      │            ├── Logs           │                    └── Modal state
      │            ├── Settings       │
      │            └── Calendar       │
      │                               │
      └───────────────────────────────┘
                   │
                   ▼
        window.pywebview.api
                   │
                   ▼
┌──────────────────────────────────────────────────────────────┐
│                   02. API / BRIDGE LAYER                     │
│                    python/gui_web/api.py                     │
└───────────────────────────────┬──────────────────────────────┘
                                │
       ┌────────────────────────┼─────────────────────────────┐
       │                        │                             │
       ▼                        ▼                             ▼
 CONNECTION                 OPERATIONS                    DATA/UI EVENTS
       │                        │                             │
       ├── connect()            ├── enrollment                ├── scan_result
       ├── disconnect()         ├── deletion                  ├── serial_line
       ├── port discovery       ├── RFID                      ├── log_line
       ├── reconnect            ├── attendance                ├── enroll_progress
       └── device status        ├── reports                   ├── delete_progress
                                ├── calendar                  ├── wipe_progress
                                ├── settings                  ├── fingerprint_count
                                ├── backup                    ├── connection_status
                                ├── restore                   ├── data_changed
                                └── authentication             └── mode_changed
                                │
                                ▼
                    ┌──────────────────────────┐
                    │     PYTHON CORE          │
                    └─────────────┬────────────┘
                                  │


══════════════════════════════════════════════════════════════════════════════════
                           03. CORE BACKEND FAMILY
══════════════════════════════════════════════════════════════════════════════════

┌───────────────────────────────┐
│        core.database          │
├───────────────────────────────┤
│                               │
│ SQLite initialization         │
│ Schema creation               │
│ Schema migration              │
│ Student validation            │
│ Student CRUD                  │
│ RFID UID linking              │
│ Attendance logging            │
│ Attendance queries            │
│ Attendance summaries          │
│ Statistics                    │
│ Reports                       │
│ CSV preparation               │
│ Chart generation              │
│ Database backup               │
│ Database restore              │
│ Destructive database actions  │
│                               │
└───────────────┬───────────────┘
                │
                ├───────────────┐
                │               │
                ▼               ▼
           students         attendance
                │               │
                │               │
                └───────┬───────┘
                        │
                        ▼
                 attendance.db


┌───────────────────────────────┐
│      core.serial_handler      │
├───────────────────────────────┤
│                               │
│ COM port management           │
│ Serial connection             │
│ Serial transmission           │
│ Serial reception              │
│ Line buffering                │
│ Device metadata               │
│ Disconnect handling            │
│ Stale-port detection          │
│ Auto reconnect                │
│                               │
└───────────────┬───────────────┘
                │
                ├── send_command()
                ├── read_line()
                └── connection state
                        │
                        ▼
                    USB Serial


┌───────────────────────────────┐
│      core.device_discovery    │
├───────────────────────────────┤
│                               │
│ Enumerate COM ports           │
│ Rank candidate ports          │
│ USB descriptor inspection     │
│ VID/PID hints                 │
│ Probe candidate               │
│ Send ID?                      │
│ Validate device identity      │
│ Validate protocol version     │
│ Adopt working device          │
│                               │
└───────────────┬───────────────┘
                │
                ▼
        Digital Student
        Identification System
                │
                ▼
             ESP32


┌───────────────────────────────┐
│         core.commands         │
├───────────────────────────────┤
│                               │
│ cmd_scan()                    │
│ cmd_stop()                    │
│ cmd_enroll()                  │
│ cmd_delete()                  │
│ cmd_wipe()                    │
│ cmd_list()                    │
│ cmd_card_write_hex()          │
│ cmd_card_erase()              │
│                               │
└───────────────┬───────────────┘
                │
                ▼
         ESP32 command API


┌───────────────────────────────┐
│        core.attendance        │
├───────────────────────────────┤
│                               │
│ Parse serial lines            │
│ Parse JSON events             │
│ Fingerprint scans             │
│ RFID scans                    │
│ Unknown scans                 │
│ Confidence classification     │
│ UID normalization             │
│ AES-GCM card validation       │
│ Duplicate protection          │
│ Cooldown handling             │
│ Attendance persistence        │
│                               │
└───────────────┬───────────────┘
                │
         ┌──────┴────────┐
         │               │
         ▼               ▼
   Fingerprint         RFID
         │               │
         └──────┬────────┘
                │
                ▼
         Attendance event
                │
                ▼
          log_attendance()
                │
                ▼
            SQLite


┌───────────────────────────────┐
│    core.attendance_status     │
├───────────────────────────────┤
│                               │
│ Time-In evaluation            │
│ Time-Out evaluation           │
│ Early calculation             │
│ Late calculation              │
│ Absent rules                  │
│ Schedule comparison           │
│                               │
└───────────────────────────────┘


┌───────────────────────────────┐
│   core.attendance_calendar    │
├───────────────────────────────┤
│                               │
│ Holidays                      │
│ Suspensions                   │
│ Half-days                     │
│ Weekday exclusions            │
│ Date-specific schedule        │
│                               │
└───────────────────────────────┘


┌───────────────────────────────┐
│          core.auth            │
├───────────────────────────────┤
│                               │
│ Password creation             │
│ Password validation            │
│ Salt generation               │
│ PBKDF2-HMAC-SHA256            │
│ Password verification         │
│ Initial admin setup           │
│                               │
└───────────────┬───────────────┘
                │
                ▼
           settings.json


┌───────────────────────────────┐
│      core.permissions         │
├───────────────────────────────┤
│                               │
│ Guest session                 │
│ Teacher session               │
│ Administrator session         │
│ Role hierarchy                │
│ Permission checks             │
│ Session timeout               │
│ Session locking               │
│                               │
└───────────────┬───────────────┘
                │
                ▼
          AUTHORIZE ACTION
                │
        ┌───────┴────────┐
        │                │
      ALLOW             DENY
        │                │
        ▼                ▼
   Continue          Return error


┌───────────────────────────────┐
│        core.rfid_card         │
├───────────────────────────────┤
│                               │
│ AES key creation              │
│ AES key storage               │
│ UID normalization             │
│ Payload creation              │
│ AES-GCM encryption            │
│ AES-GCM decryption            │
│ Authentication tag check      │
│ Payload version validation    │
│ Student identity extraction   │
│                               │
└────────────────────────────────┘


┌───────────────────────────────┐
│        core.logger            │
├───────────────────────────────┤
│                               │
│ Console logging               │
│ File logging                  │
│ Timestamped runs              │
│ UI log buffering              │
│ Runtime diagnostics           │
│ Exception logging             │
│                               │
└───────────────────────────────┘


┌───────────────────────────────┐
│     core.setup_wizard         │
├───────────────────────────────┤
│                               │
│ Password step                 │
│ Device step                   │
│ Schedule step                 │
│ Branding step                 │
│ Resume interrupted setup      │
│                               │
└───────────────────────────────┘


┌───────────────────────────────┐
│      core.firmware_helper     │
├───────────────────────────────┤
│ Firmware candidate discovery  │
│ Firmware information          │
│ Upload/build helpers          │
└───────────────────────────────┘


┌───────────────────────────────┐
│          core.utils           │
├───────────────────────────────┤
│                               │
│ JSON-line parsing             │
│ Shared conversion helpers     │
│ Small runtime utilities       │
│                               │
└───────────────────────────────┘


══════════════════════════════════════════════════════════════════════════════════
                              04. SERVICE FAMILY
══════════════════════════════════════════════════════════════════════════════════

                   ┌─────────────────────────────┐
                   │       python/services       │
                   └──────────────┬──────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
          student_service.py          attendance_service.py
                    │                           │
                    ▼                           ▼
            Student operations          Attendance operations
                    │                           │
                    └─────────────┬─────────────┘
                                  ▼
                              Core layer


══════════════════════════════════════════════════════════════════════════════════
                              05. HARDWARE FAMILY
══════════════════════════════════════════════════════════════════════════════════

                 ┌─────────────────────────────────┐
                 │        ESP32 WROOM-32            │
                 │       DSIS All-In-One            │
                 └────────────────┬────────────────┘
                                  │
             ┌────────────────────┼────────────────────┐
             │                    │                    │
             ▼                    ▼                    ▼
        USB Serial              UART 2              SPI BUS
         115200                  57600                  │
             │                    │                    │
             │                    ▼                    ▼
             │                AS608                RC522
             │
             ▼
       Python application


══════════════════════════════════════════════════════════════════════════════════
                         06. ESP32 FIRMWARE FAMILY
══════════════════════════════════════════════════════════════════════════════════

                 ┌──────────────────────────────────┐
                 │ ESP32_DSIS_AllInOne.ino          │
                 └────────────────┬─────────────────┘
                                  │
          ┌───────────────────────┼────────────────────────┐
          │                       │                        │
          ▼                       ▼                        ▼
    Host Interface          Fingerprint Engine          RFID Engine
          │                       │                        │
          │                       │                        │
          ├── ID?                 ├── getImage()           ├── Detect card
          ├── SCAN                ├── image2Tz()           ├── Read UID
          ├── STOP                ├── fingerSearch()       ├── Detect type
          ├── ENROLL              ├── createModel()        ├── Authenticate
          ├── ENROLL:<id>         ├── storeModel()         ├── Read payload
          ├── DELETE:<id>         ├── loadModel()          ├── Write payload
          ├── WIPE                ├── deleteModel()        └── Verify readback
          ├── LIST                └── template count
          ├── CARD_WRITE_HEX
          ├── CARD_ERASE
          └── STATUS:<state>
                                  │
                                  ▼
                         Structured JSON events


══════════════════════════════════════════════════════════════════════════════════
                          07. FINGERPRINT FAMILY
══════════════════════════════════════════════════════════════════════════════════

                              ┌──────────┐
                              │  AS608   │
                              └────┬─────┘
                                   │
                ┌──────────────────┴──────────────────┐
                │                                     │
                ▼                                     ▼
          ENROLLMENT                            ATTENDANCE
                │                                     │
                ▼                                     ▼
          Find free ID                          Place finger
                │                                     │
                ▼                                     ▼
         Capture finger #1                       getImage()
                │                                     │
                ▼                                     ▼
           image2Tz(1)                           image2Tz()
                │                                     │
                ▼                                     ▼
         Remove finger                           Search DB
                │                                     │
                ▼                           ┌─────────┴─────────┐
         Capture finger #2                   │                   │
                │                         MATCH               NO MATCH
                ▼                           │                   │
           image2Tz(2)                      │                   ▼
                │                           │                UNKNOWN
                ▼                           │
          createModel()                     ▼
                │                       Confidence
        ┌───────┴────────┐                  │
        │                │          ┌───────┴───────┐
     MATCH            MISMATCH      │               │
        │                │        >= minimum      < minimum
        ▼                ▼           │               │
   storeModel()       ERROR          ▼               ▼
        │                         GOOD MATCH     LOW CONFIDENCE
        ▼
  Enrollment success


══════════════════════════════════════════════════════════════════════════════════
                            08. RFID FAMILY
══════════════════════════════════════════════════════════════════════════════════

                              ┌──────────┐
                              │  RC522   │
                              └────┬─────┘
                                   │
                                   ▼
                           Read Card + UID
                                   │
                                   ▼
                         ┌──────────────────┐
                         │   CardDetector   │
                         └────────┬─────────┘
                                  │
       ┌──────────────────────────┼─────────────────────────────┐
       │                          │                             │
       ▼                          ▼                             ▼
   CLASSIC                      TYPE 2                        OTHER
       │                          │                             │
       │                          │                             └── Unsupported
       │                          │                                  │
       │                          ▼                                  ▼
       │                   Inspect Type 2                      card_unreadable
       │                      metadata
       │                          │
       │             ┌────────────┼─────────────┐
       │             │            │             │
       │        Ultralight      NTAG215       NTAG216
       │             │            │             │
       │             └────────────┴─────────────┘
       │                          │
       │                          ▼
       │                    Type2Adapter
       │
       ▼
  ClassicAdapter
       │
       ├── MIFARE Mini
       ├── MIFARE 1K
       └── MIFARE 4K
       │
       ├── Authenticate sector
       │
       ├── Read blocks 4-6
       │
       ├── Write blocks 4-6
       │
       └── Verify readback
                                  │
                                  ▼
                          48-byte payload


══════════════════════════════════════════════════════════════════════════════════
                         09. RFID ATTENDANCE FAMILY
══════════════════════════════════════════════════════════════════════════════════

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
                    ┌───────────┴───────────┐
                    │                       │
                Supported               Unsupported
                    │                       │
                    ▼                       ▼
                Adapter                 UNKNOWN
                    │
             ┌──────┴──────┐
             │             │
          Classic         Type2
             │             │
             ▼             ▼
          Read 48B       Read 48B
             │             │
             └──────┬──────┘
                    ▼
             Encrypted payload
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
                    ▼
             Normalize UID
                    │
                    ▼
             AES-GCM decrypt
                    │
          ┌─────────┴─────────┐
          │                   │
       INVALID              VALID
          │                   │
          ▼                   ▼
       UNKNOWN         Extract identity
                            │
                   ┌────────┴────────┐
                   │                 │
             fingerprint_id      student_no
                   │                 │
                   └────────┬────────┘
                            ▼
                     Student lookup
                            │
                            ▼
                     Identity agreement
                            │
              ┌─────────────┴─────────────┐
              │                           │
            FAIL                         PASS
              │                           │
              ▼                           ▼
           UNKNOWN                   Cooldown check
                                          │
                              ┌───────────┴───────────┐
                              │                       │
                           BLOCKED                 ALLOWED
                              │                       │
                              ▼                       ▼
                          Ignore duplicate       Log attendance
                                                      │
                                                      ▼
                                                  SQLite


══════════════════════════════════════════════════════════════════════════════════
                         10. RFID REGISTRATION FAMILY
══════════════════════════════════════════════════════════════════════════════════

                       Select Student
                             │
                             ▼
               start_rfid_register_session()
                             │
             ┌───────────────┼────────────────┐
             │               │                │
          Permission      Student exists   No conflict
             │               │                │
             └───────────────┴────────────────┘
                             │
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
                 ┌───────────┴───────────┐
                 │                       │
             Already linked           Available
                 │                       │
                 ▼                       ▼
               Reject             Build payload
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
                          ┌──────────────┴──────────────┐
                          │                             │
                       Classic                        Type2
                          │                             │
                       Write blocks                 Write pages
                          │                             │
                          └──────────────┬──────────────┘
                                         ▼
                                  Readback verify
                                         │
                                         ▼
                                   write_verified
                                         │
                                         ▼
                              Python verification
                                         │
             ┌───────────────────────────┼──────────────────────────┐
             │                           │                          │
          UID match                Payload match               Verified flag
             │                           │                          │
             └───────────────────────────┴──────────────────────────┘
                                         │
                                         ▼
                              db.bind_student_card()
                                         │
                                         ▼
                              Student ↔ Card UID


══════════════════════════════════════════════════════════════════════════════════
                           11. ENROLLMENT FAMILY
══════════════════════════════════════════════════════════════════════════════════

                      Student information
                             │
                             ▼
                   Validate input fields
                             │
                             ▼
                       start_enroll()
                             │
                             ▼
                     Permission check
                             │
                             ▼
                    Conflict check
                             │
                             ▼
                         STOP scan
                             │
                             ▼
                           ENROLL
                             │
                             ▼
                          ESP32
                             │
                             ▼
                    Find free fingerprint ID
                             │
                             ▼
                       AS608 enrollment
                             │
               ┌─────────────┴─────────────┐
               │                           │
             FAILED                      SUCCESS
               │                           │
               ▼                           ▼
        mismatch/error              storeModel(ID)
                                           │
                                           ▼
                                   enrollment event
                                           │
                                           ▼
                                    Python receives ID
                                           │
                                           ▼
                                      save_student()
                                           │
                                           ▼
                                      SQLite student


══════════════════════════════════════════════════════════════════════════════════
                           12. ATTENDANCE FAMILY
══════════════════════════════════════════════════════════════════════════════════

                 ┌────────────────────────────┐
                 │       IDENTIFICATION       │
                 └─────────────┬──────────────┘
                               │
                  ┌────────────┴────────────┐
                  │                         │
                  ▼                         ▼
             Fingerprint                  RFID
                  │                         │
                  ▼                         ▼
               AS608                     RC522
                  │                         │
                  └────────────┬────────────┘
                               ▼
                       AttendanceProcessor
                               │
                    ┌──────────┴───────────┐
                    │                      │
               Known identity         Unknown identity
                    │                      │
                    ▼                      ▼
              Cooldown check            UNKNOWN
                    │
           ┌────────┴────────┐
           │                 │
        Duplicate         Allowed
           │                 │
           ▼                 ▼
         Ignore         Record event
                               │
                               ▼
                          event_type
                               │
                    ┌──────────┴──────────┐
                    │                     │
                 time_in               time_out
                    │                     │
                    └──────────┬──────────┘
                               ▼
                        attendance table


══════════════════════════════════════════════════════════════════════════════════
                            13. DELETE FAMILY
══════════════════════════════════════════════════════════════════════════════════

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
                                ▼
                         Load fingerprint
                                │
                       ┌────────┴────────┐
                       │                 │
                    EXISTS            MISSING
                       │                 │
                       ▼                 ▼
                  Delete model        FAILED
                       │
                       ▼
                    SUCCESS
                       │
                       ▼
                 Local database
                       │
             ┌─────────┴─────────┐
             │                   │
        Student row         Old attendance
          deleted             preserved
                                 │
                                 ▼
                          fingerprint_id = 0
                                 │
                                 ▼
                            Unregistered


══════════════════════════════════════════════════════════════════════════════════
                              14. WIPE FAMILY
══════════════════════════════════════════════════════════════════════════════════

                             WIPE REQUEST
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
              DEVICE DOMAIN                LOCAL DOMAIN
                    │                           │
                    ▼                           ▼
                 ESP32                    wipe_all_data()
                    │                           │
                    ▼                    Permission check
            Clear fingerprint                │
               templates                      ▼
                    │                    Delete attendance
                    ▼                           │
                Success                         ▼
                    │                    Delete students
                    │                           │
                    └──────────────┬────────────┘
                                   ▼
                              ID 0 remains
                                   │
                                   ▼
                             Unregistered


══════════════════════════════════════════════════════════════════════════════════
                             15. DATABASE FAMILY
══════════════════════════════════════════════════════════════════════════════════

                        data/attendance.db
                               │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
                students              attendance
                    │                     │
                    │                     ├── id
                    ├── fingerprint_id    ├── fingerprint_id
                    ├── student_no        ├── date
                    ├── student_name      ├── time
                    ├── grade             ├── confidence
                    ├── section           ├── status
                    ├── card_uid          ├── timestamp
                    ├── enrollment_date   └── event_type
                    └── updated_date           │
                                                │
                                      ┌─────────┴─────────┐
                                      │                   │
                                   time_in             time_out

 RELATIONSHIP

 students.fingerprint_id
            │
            ▼
 attendance.fingerprint_id


 SPECIAL IDENTITY

 0
 │
 └── Unregistered / Unknown

 1–127
 │
 └── Real AS608 student template IDs


══════════════════════════════════════════════════════════════════════════════════
                            16. SETTINGS FAMILY
══════════════════════════════════════════════════════════════════════════════════

                         data/settings.json
                                │
        ┌───────────────────────┼─────────────────────────┐
        │                       │                         │
        ▼                       ▼                         ▼
     DEVICE                  ATTENDANCE                 UI
        │                       │                         │
        ├── com_port            ├── cooldown              ├── theme
        ├── baud_rate           ├── min_confidence        ├── branding
        ├── auto_detect         ├── time_in               └── sidebar
        └── auto_reconnect      ├── time_out
                                ├── early threshold
                                ├── late threshold
                                └── absent threshold

        │
        ├───────────────────────┬────────────────────────────┐
        │                       │                            │
        ▼                       ▼                            ▼
      CALENDAR                BACKUP                    SETUP STATE
        │                       │                            │
        ├── holidays            └── interval                 ├── device done
        ├── suspensions                                      ├── schedule done
        ├── half-days                                         └── branding done
        └── weekday exclusions

        │
        ▼
     AUTH DATA
        │
        └── password hash / salt / iteration data


══════════════════════════════════════════════════════════════════════════════════
                         17. AUTHENTICATION FAMILY
══════════════════════════════════════════════════════════════════════════════════

                         FIRST RUN
                            │
                            ▼
                     Create password
                            │
                            ▼
                       Hash password
                            │
                            ▼
                       Save auth data
                            │
                            ▼
                    Administrator session
                            │
                            ▼
                     Normal application


                         RUNTIME
                            │
                            ▼
                         SESSION
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
            Guest        Teacher        Admin
              │             │             │
              └─────────────┼─────────────┘
                            ▼
                     Permission check
                            │
                    ┌───────┴────────┐
                    │                │
                 Allowed           Denied
                    │                │
                    ▼                ▼
                Operation          Error
                    │
                    ▼
              Idle timeout
                    │
                    ▼
                  Guest


══════════════════════════════════════════════════════════════════════════════════
                            18. REPORTING FAMILY
══════════════════════════════════════════════════════════════════════════════════

                         SQLite data
                              │
                              ▼
                       Reporting layer
                              │
       ┌──────────────────────┼───────────────────────────────┐
       │                      │                               │
       ▼                      ▼                               ▼
 ATTENDANCE REPORT       STATISTICS                     EVALUATION
       │                      │                               │
       ├── Daily              ├── Total students             ├── Day
       ├── Weekly             ├── Attendance totals          ├── Week
       ├── Monthly            ├── By grade                   └── Month
       └── Time In/Out        ├── By section
                              └── Timeline
       │
       └───────────────┬───────────────┐
                       │               │
                       ▼               ▼
                     CSV             Charts
                       │               │
                       └───────┬───────┘
                               ▼
                         Export files


══════════════════════════════════════════════════════════════════════════════════
                             19. BACKUP FAMILY
══════════════════════════════════════════════════════════════════════════════════

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
                   ┌──────────┴───────────┐
                   │                      │
              Validate path          Validate SQLite
                   │                      │
                   └──────────┬───────────┘
                              ▼
                         Replace DB
                              │
                              ▼
                       data/attendance.db


══════════════════════════════════════════════════════════════════════════════════
                             20. LOGGING FAMILY
══════════════════════════════════════════════════════════════════════════════════

                           core.logger
                               │
           ┌───────────────────┼────────────────────┐
           │                   │                    │
           ▼                   ▼                    ▼
        Console             File logs            UI buffer
           │                   │                    │
           │                   ▼                    ▼
           │               data/logs/          log_line
           │
           ├── startup
           ├── device
           ├── serial
           ├── attendance
           ├── security
           ├── errors
           └── diagnostics


══════════════════════════════════════════════════════════════════════════════════
                            21. RUNTIME THREADS
══════════════════════════════════════════════════════════════════════════════════

                         DSIS PROCESS
                              │
            ┌─────────────────┼───────────────────────┐
            │                 │                       │
            ▼                 ▼                       ▼
        Main UI          Serial Reader          Background Workers
            │                 │                       │
            │                 │                ┌──────┴────────┐
            │                 │                │               │
            │                 ▼                ▼               ▼
            │          Read ESP32 lines   Auto Backup    Reconnect
            │                 │
            │                 ▼
            │          Parse events
            │                 │
            │                 ▼
            │          AttendanceProcessor
            │
            ▼
         pywebview
            │
            ▼
          app.js


══════════════════════════════════════════════════════════════════════════════════
                         22. RUNTIME DATA FAMILY
══════════════════════════════════════════════════════════════════════════════════

                               data/
                                │
          ┌───────────────┬─────┴────────┬──────────────┬─────────────┐
          │               │              │              │             │
          ▼               ▼              ▼              ▼             ▼
   attendance.db      settings.json   backups/        logs/        exports/
          │               │              │              │             │
          │               │              │              │             │
          │               │              │              └── runtime logs
          │               │              └── DB snapshots
          │               └── config/auth/session continuity
          └── students + attendance

                                │
                                ▼
                             charts/
                                │
                                └── generated report graphics

                                │
                                ▼
                      .admin_initialized
                                │
                                └── first-admin setup marker


══════════════════════════════════════════════════════════════════════════════════
                            23. TESTING FAMILY
══════════════════════════════════════════════════════════════════════════════════

                              tests/
                                │
        ┌───────────────────────┼───────────────────────────────┐
        │                       │                               │
        ▼                       ▼                               ▼
     UNIT TESTS             GUI TESTS                     HARDWARE TESTS
        │                       │                               │
        ├── attendance          ├── web GUI smoke              ├── ESP32 smoke
        ├── database            ├── Qt compatibility            ├── serial tests
        ├── authentication      ├── responsive UI              ├── sensor failures
        ├── permissions         ├── enrollment dialogs          └── firmware tests
        ├── serial              ├── settings
        ├── RFID                ├── logs
        └── validation          └── student pages
                                │
                                ▼
                         Regression coverage


                        SPECIAL TEST AREAS
                                │
        ┌───────────────────────┼───────────────────────────────┐
        │                       │                               │
        ▼                       ▼                               ▼
     Security               Integration                    Protocol
        │                       │                               │
        ├── DB security        ├── GUI ↔ API                  ├── firmware protocol
        ├── auth               ├── API ↔ DB                   ├── attendance parsing
        ├── permissions        ├── API ↔ serial               └── serial behavior
        └── error handling     └── API ↔ RFID


══════════════════════════════════════════════════════════════════════════════════
                              24. BUILD FAMILY
══════════════════════════════════════════════════════════════════════════════════

                              Build/
                                │
           ┌────────────────────┼────────────────────┐
           │                    │                    │
           ▼                    ▼                    ▼
      DSIS_v1.spec         DSIS_v2.spec         DSIS_v3.spec
                                                     │
                                                     ▼
                                                ACTIVE BUILD
                                                     │
                                                     ▼
                                                  PyInstaller
                                                     │
                                                     ▼
                                            Windows distribution


                        SUPPORTING BUILD FILES
                                │
                                ├── fingerprint_portable.spec
                                ├── build output
                                ├── portable build docs
                                └── release documentation


══════════════════════════════════════════════════════════════════════════════════
                             25. TOOLS FAMILY
══════════════════════════════════════════════════════════════════════════════════

                              tools/
                                │
       ┌────────────────────────┼───────────────────────────┐
       │                        │                           │
       ▼                        ▼                           ▼
   Database tools          Serial tools                Runtime tools
       │                        │                           │
       ├── DB refactor          ├── port probe             ├── runtime manager
       ├── DB connection debug  ├── pipeline tester        ├── GUI startup
       └── archive scripts      └── worker probes          └── verify scripts
                                │
                                ▼
                         Forensics / diagnostics
                                │
                                └── copilot forensic search


══════════════════════════════════════════════════════════════════════════════════
                           26. FIRMWARE FAMILY
══════════════════════════════════════════════════════════════════════════════════

                              firmware/
                                  │
          ┌───────────────────────┼─────────────────────────┐
          │                       │                         │
          ▼                       ▼                         ▼
   ACTIVE ALL-IN-ONE       EARLIER FIRMWARE            TEST SKETCHES
          │                       │                         │
          │                       └── ESP32_Fingerprint     ├── rc522_test
          │                           _AllInOne             ├── rc522_read
          │                                                   ├── rc522_write
          ▼                                                   ├── rc522_readwrite
 ESP32_DSIS_AllInOne                                      ├── rc522_dumpinfo
          │                                                 ├── fingerprint_check
          ├── AS608                                           └── other hardware tests
          ├── RC522
          ├── LED manager
          ├── command engine
          ├── scan engine
          └── JSON protocol


══════════════════════════════════════════════════════════════════════════════════
                           27. DOCUMENTATION FAMILY
══════════════════════════════════════════════════════════════════════════════════

                              docs/
                                │
       ┌────────────────────────┼─────────────────────────────┐
       │                        │                             │
       ▼                        ▼                             ▼
   Architecture             Hardware                    Development
       │                        │                             │
       ├── system architecture ├── wiring                     ├── setup
       ├── runtime contract    ├── connections                ├── testing
       ├── software flow       ├── serial protocol             ├── implementation
       ├── DB schema           ├── firmware variants            ├── logging
       ├── bridge              └── drivers / ports              ├── runtime data
       └── V3 details                                             └── changelog
       │
       ├─────────────────────┐
       ▼                     ▼
    Hardware              History
       │                     │
       └── RFID              ├── V1 lineage
                             ├── V2 lineage
                             └── V3 migration


══════════════════════════════════════════════════════════════════════════════════
                            28. REPOSITORY FAMILY
══════════════════════════════════════════════════════════════════════════════════

                              REPOSITORY
                                  │
      ┌───────────────────────────┼─────────────────────────────────┐
      │                           │                                 │
      ▼                           ▼                                 ▼
   Runtime                     Support                         History
      │                           │                                 │
      ├── python/                 ├── tests/                         └── archive/
      ├── firmware/               ├── tools/                             │
      ├── data/ (runtime only)    ├── Build/                            ├── legacy-ui/v1
      └── root launchers          └── docs/                             ├── legacy-ui/v2
                                                                          ├── diagnostics
                                                                          └── old prototypes


══════════════════════════════════════════════════════════════════════════════════
                           29. VERSION LINEAGE
══════════════════════════════════════════════════════════════════════════════════

                                  DSIS
                                   │
                  ┌────────────────┼────────────────┐
                  │                │                │
                  ▼                ▼                ▼
                 V1               V2               V3
                  │                │                │
             CustomTkinter     PySide6 / Qt      HTML + JS
                  │                │                │
                  │                │                ▼
                  │                │             pywebview
                  │                │                │
                  └───────┬────────┘                ▼
                          │                   Python backend
                          │                        │
                          │              ┌─────────┼──────────┐
                          │              │         │          │
                          │              ▼         ▼          ▼
                          │           Database   Serial    Attendance
                          │
                          ▼
                    Archived lineage
                          │
                          ▼
                    Reference only


══════════════════════════════════════════════════════════════════════════════════
                             30. COMPLETE DATA FLOW
══════════════════════════════════════════════════════════════════════════════════

                     STUDENT / STAFF ACTION
                              │
                              ▼
                            Web UI
                              │
                              ▼
                         pywebview API
                              │
                              ▼
                           Api class
                              │
                 ┌────────────┼──────────────┐
                 │            │              │
                 ▼            ▼              ▼
            Permissions    Core logic     Serial
                 │            │              │
                 │            │              ▼
                 │            │            ESP32
                 │            │              │
                 │            │       ┌──────┴───────┐
                 │            │       │              │
                 │            │      AS608          RC522
                 │            │       │              │
                 │            │       └──────┬───────┘
                 │            │              │
                 │            └──────────────┘
                 │                           │
                 │                           ▼
                 │                    Structured event
                 │                           │
                 └───────────────────────────┤
                                             ▼
                                      AttendanceProcessor
                                             │
                                ┌────────────┴────────────┐
                                │                         │
                           Fingerprint                 RFID
                                │                         │
                                │                    AES-GCM validation
                                │                         │
                                └────────────┬────────────┘
                                             ▼
                                       Student identity
                                             │
                                             ▼
                                      SQLite attendance
                                             │
                     ┌───────────────────────┼──────────────────────┐
                     │                       │                      │
                     ▼                       ▼                      ▼
                 Dashboard              Attendance              Reports
                     │                       │                      │
                     └───────────────────────┼──────────────────────┘
                                             ▼
                                              UI
                                             │
                                             ▼
                                      User sees result


══════════════════════════════════════════════════════════════════════════════════
                              31. FAILURE PATH
══════════════════════════════════════════════════════════════════════════════════

                              ANY OPERATION
                                  │
                                  ▼
                              Validation
                                  │
                       ┌──────────┴──────────┐
                       │                     │
                    VALID                  INVALID
                       │                     │
                       ▼                     ▼
                   Continue               Reject
                       │
                       ▼
                 Hardware / DB
                       │
                 ┌─────┴─────┐
                 │           │
               SUCCESS      ERROR
                 │           │
                 ▼           ▼
              Persist      Log error
                 │           │
                 ▼           ▼
               Notify       Notify UI
                 │           │
                 └─────┬─────┘
                       ▼
                      UI


══════════════════════════════════════════════════════════════════════════════════
                             32. SYSTEM BOUNDARY
══════════════════════════════════════════════════════════════════════════════════

                   ┌────────────────────────────────────┐
                   │             DSIS DESKTOP            │
                   │                                    │
                   │  HTML / JS                         │
                   │       ↓                            │
                   │  pywebview                         │
                   │       ↓                            │
                   │  Python API                        │
                   │       ↓                            │
                   │  Core backend                      │
                   │       ↓                            │
                   │  SQLite / Filesystem               │
                   │                                    │
                   └────────────────┬───────────────────┘
                                    │
                               USB Serial
                                    │
                                    ▼
                   ┌────────────────────────────────────┐
                   │              ESP32                  │
                   │                                    │
                   │  Command engine                    │
                   │  Fingerprint engine                │
                   │  RFID engine                       │
                   │  LED engine                        │
                   │  JSON serial protocol              │
                   │                                    │
                   └───────────────┬───────────┬────────┘
                                   │           │
                                UART 57600   SPI
                                   │           │
                                   ▼           ▼
                                 AS608       RC522
                                   │           │
                                   └─────┬─────┘
                                         ▼
                                   IDENTIFICATION


══════════════════════════════════════════════════════════════════════════════════
                              FINAL ARCHITECTURE
══════════════════════════════════════════════════════════════════════════════════

                                DSIS
                                 │
       ┌─────────────────────────┼───────────────────────────┐
       │                         │                           │
       ▼                         ▼                           ▼
     USER                    SOFTWARE                    HARDWARE
       │                         │                           │
       │                         ├── UI                      ├── ESP32
       │                         ├── API                     ├── AS608
       │                         ├── Core                    └── RC522
       │                         ├── Services
       │                         ├── Database
       │                         ├── Auth
       │                         ├── Reports
       │                         └── Settings
       │
       ▼
 IDENTIFICATION
       │
       ├──────────────────────┬──────────────────────┐
       │                      │                      │
       ▼                      ▼                      ▼
  Fingerprint               RFID                 Future ID
       │                      │
       ▼                      ▼
      AS608                  RC522
       │                      │
       └──────────────┬───────┘
                      ▼
                 DEVICE EVENT
                      │
                      ▼
                SERIAL PROTOCOL
                      │
                      ▼
                PYTHON PROCESSOR
                      │
             ┌────────┴────────┐
             │                 │
        Validate            Identify
             │                 │
             └────────┬────────┘
                      ▼
                  SQLite
                      │
          ┌───────────┼───────────┐
          │           │           │
          ▼           ▼           ▼
       Records     Reports     Statistics
          │           │           │
          └───────────┼───────────┘
                      ▼
                    WEB UI
                      │
                      ▼
                  USER RESULT,```,## Lineage tree — `f0b0074` → `c2eb4d3`

```text
ARCHITECTURE / DOCUMENTATION LINEAGE
│
├── 01. f0b0074 — docs: add complete DSIS system architecture  [START]
├── 02. 51a2ed6 — docs: link complete system architecture from README
├── 03. bf47107 — docs: add complete architecture to documentation index
├── 04. 9121297 — docs: add full repository architecture tree
├── 05. ea0c2b6 — docs: map firmware and core symbols
├── 06. 2ba2a64 — docs: map backend and GUI symbols
├── 07. 807febe — docs: map GUI and reference symbols
├── 08. da8e4a8 — docs: map remaining production symbols
├── 09. c189d4a — docs: finish production symbol tree
├── 10. b21e7b6 — docs: map prototype and UI test symbols
├── 11. b072332 — docs: expand more test symbols
├── 12. 15949e6 — docs: link full project symbol tree
├── 13. 047d473 — docs: index full project symbol tree
├── 14. 43dd4c4 — docs: expand core test symbols A
├── 15. b522cb9 — docs: expand core test symbols B
├── 16. 010720d — docs: expand core test symbols C
├── 17. de2d23c — docs: finish full test symbol tree
├── 18. 2cd0ea5 — docs: refresh complete repository tree
├── 19. bd0d26f — docs: map archive symbols A
├── 20. 9850a85 — docs: map archive symbols B
├── 21. d274af8 — docs: map archive symbols C
├── 22. 3869955 — docs: map archive symbols D
├── 23. 5de830e — docs: map archive symbols E
├── 24. a6cebd8 — docs: map archive symbols F
├── 25. becb1f9 — docs: map archive symbols G
├── 26. e9e03af — docs: map archive symbols H
├── 27. 940478d — docs: map archive symbols I
├── 28. 10516a6 — docs: map archive symbols J
├── 29. 16b931c — docs: finish exhaustive archive symbols
├── 30. a4b3f4b — docs: add visual project architecture tree
├── 31. dc0d128 — docs: link visual architecture tree
├── 32. c2eb4d3 — docs: index visual architecture tree
├── 33. 83a29da — docs: rebuild full architecture tree from current main  [CURRENT]
```

The lineage contains 33 commits from the requested starting point `f0b0074` through the current branch. The requested starting commit is an architecture-document baseline, not the historical first commit of DSIS. Documentation repair commits after the snapshot are intentionally excluded from the architecture lineage so the diagram describes the project rather than the editing session.

## Exact current repository tree

> This appendix is the filesystem/path branch corresponding to the architecture above. It is regenerated from the live `main` Git tree.

```text
Digital-Student-Identification-System/
  ├── .github/
  │   ├── instructions/
  │   │   └── SKILL.instructions.md
  │   └── workflows/
  │       └── tests.yml
  ├── archive/
  │   ├── diagnostics/
  │   │   ├── discovery_handshake_probe.py
  │   │   ├── serial_monitor_test.py
  │   │   ├── serial_pipeline_tester.py
  │   │   ├── temp_serial_port_info.py
  │   │   ├── tmp_serial_dtr_test.py
  │   │   ├── tmp_serial_handler_probe.py
  │   │   └── tmp_serial_probe.py
  │   ├── legacy-ui/
  │   │   ├── gui_qt_redesign/
  │   │   │   ├── gui_qt/
  │   │   │   │   ├── pages/
  │   │   │   │   │   ├── __init__.py
  │   │   │   │   │   ├── attendance_page.py
  │   │   │   │   │   ├── dashboard_page.py
  │   │   │   │   │   ├── logs_page.py
  │   │   │   │   │   ├── reports_page.py
  │   │   │   │   │   ├── settings_page.py
  │   │   │   │   │   └── students_page.py
  │   │   │   │   ├── widgets/
  │   │   │   │   │   ├── __init__.py
  │   │   │   │   │   ├── sidebar.py
  │   │   │   │   │   └── stat_card.py
  │   │   │   │   ├── workers/
  │   │   │   │   │   ├── __init__.py
  │   │   │   │   │   └── serial_worker.py
  │   │   │   │   ├── __init__.py
  │   │   │   │   ├── main_qt.py
  │   │   │   │   ├── main_window.py
  │   │   │   │   └── theme.qss
  │   │   │   └── README.md
  │   │   ├── gui_qt_redesign_2/
  │   │   │   ├── gui_qt/
  │   │   │   │   ├── pages/
  │   │   │   │   │   ├── __init__.py
  │   │   │   │   │   ├── attendance_page.py
  │   │   │   │   │   ├── dashboard_page.py
  │   │   │   │   │   ├── logs_page.py
  │   │   │   │   │   ├── reports_page.py
  │   │   │   │   │   ├── settings_page.py
  │   │   │   │   │   └── students_page.py
  │   │   │   │   ├── widgets/
  │   │   │   │   │   ├── __init__.py
  │   │   │   │   │   ├── sidebar.py
  │   │   │   │   │   └── stat_card.py
  │   │   │   │   ├── workers/
  │   │   │   │   │   ├── __init__.py
  │   │   │   │   │   └── serial_worker.py
  │   │   │   │   ├── __init__.py
  │   │   │   │   ├── main_qt.py
  │   │   │   │   ├── main_window.py
  │   │   │   │   └── theme.qss
  │   │   │   └── README.md
  │   │   ├── testing_area/
  │   │   │   ├── core/
  │   │   │   │   └── database_addition_snippet.py
  │   │   │   ├── gui/
  │   │   │   │   └── legacy/
  │   │   │   │       ├── app_test.py
  │   │   │   │       ├── app_test1.py
  │   │   │   │       ├── bfeas_app.py
  │   │   │   │       ├── bfeas_app2.py
  │   │   │   │       └── reports_table_page.py
  │   │   │   ├── services/
  │   │   │   │   ├── backup.py
  │   │   │   │   └── excel_export.py
  │   │   │   └── README.txt
  │   │   ├── v1/
  │   │   │   ├── python/
  │   │   │   │   ├── core/
  │   │   │   │   │   ├── __init__.py
  │   │   │   │   │   ├── attendance.py
  │   │   │   │   │   ├── commands.py
  │   │   │   │   │   ├── database.py
  │   │   │   │   │   ├── logger.py
  │   │   │   │   │   ├── serial_handler.py
  │   │   │   │   │   └── utils.py
  │   │   │   │   ├── gui/
  │   │   │   │   │   ├── __init__.py
  │   │   │   │   │   ├── app.py
  │   │   │   │   │   ├── attendance_page.py
  │   │   │   │   │   ├── dashboard.py
  │   │   │   │   │   ├── dialogs.py
  │   │   │   │   │   ├── log_page.py
  │   │   │   │   │   ├── main_window.py
  │   │   │   │   │   ├── reports_page.py
  │   │   │   │   │   ├── settings_dialog.py
  │   │   │   │   │   ├── settings_page.py
  │   │   │   │   │   ├── sidebar.py
  │   │   │   │   │   ├── statistics_page.py
  │   │   │   │   │   ├── students_page.py
  │   │   │   │   │   ├── theme.py
  │   │   │   │   │   └── widgets.py
  │   │   │   │   ├── services/
  │   │   │   │   │   ├── __init__.py
  │   │   │   │   │   ├── attendance_service.py
  │   │   │   │   │   ├── backup.py
  │   │   │   │   │   ├── excel_export.py
  │   │   │   │   │   └── student_service.py
  │   │   │   │   ├── __init__.py
  │   │   │   │   ├── config.py
  │   │   │   │   ├── fix_emoji.py
  │   │   │   │   ├── main.py
  │   │   │   │   └── settings_store.py
  │   │   │   ├── README.md
  │   │   │   └── run_app.bat
  │   │   └── v2/
  │   │       ├── python/
  │   │       │   ├── core/
  │   │       │   │   ├── __init__.py
  │   │       │   │   ├── attendance.py
  │   │       │   │   ├── commands.py
  │   │       │   │   ├── database.py
  │   │       │   │   ├── device_discovery.py
  │   │       │   │   ├── firmware_helper.py
  │   │       │   │   ├── logger.py
  │   │       │   │   ├── permissions.py
  │   │       │   │   ├── serial_handler.py
  │   │       │   │   └── utils.py
  │   │       │   ├── gui/
  │   │       │   │   ├── legacy/
  │   │       │   │   │   ├── bfeas_app2.py
  │   │       │   │   │   └── reports_table_page.py
  │   │       │   │   ├── __init__.py
  │   │       │   │   ├── app.py
  │   │       │   │   ├── attendance_page.py
  │   │       │   │   ├── dashboard.py
  │   │       │   │   ├── dialogs.py
  │   │       │   │   ├── layout_utils.py
  │   │       │   │   ├── log_page.py
  │   │       │   │   ├── perf_profiler.py
  │   │       │   │   ├── reports_page.py
  │   │       │   │   ├── serial_troubleshooting.py
  │   │       │   │   ├── settings_dialog.py
  │   │       │   │   ├── settings_page.py
  │   │       │   │   ├── sidebar.py
  │   │       │   │   ├── statistics_page.py
  │   │       │   │   ├── students_page.py
  │   │       │   │   └── theme.py
  │   │       │   ├── gui_qt/
  │   │       │   │   ├── pages/
  │   │       │   │   │   ├── __init__.py
  │   │       │   │   │   ├── attendance_page.py
  │   │       │   │   │   ├── dashboard_page.py
  │   │       │   │   │   ├── logs_page.py
  │   │       │   │   │   ├── reports_page.py
  │   │       │   │   │   ├── settings_page.py
  │   │       │   │   │   └── students_page.py
  │   │       │   │   ├── widgets/
  │   │       │   │   │   ├── __init__.py
  │   │       │   │   │   ├── sidebar.py
  │   │       │   │   │   └── stat_card.py
  │   │       │   │   ├── workers/
  │   │       │   │   │   ├── __init__.py
  │   │       │   │   │   ├── connection_worker.py
  │   │       │   │   │   └── serial_worker.py
  │   │       │   │   ├── __init__.py
  │   │       │   │   ├── main_qt.py
  │   │       │   │   ├── main_window.py
  │   │       │   │   ├── theme_light.qss
  │   │       │   │   └── theme.qss
  │   │       │   ├── non_workflow/
  │   │       │   │   ├── fix_emoji.py
  │   │       │   │   ├── main_window.py
  │   │       │   │   ├── serial.py
  │   │       │   │   └── widgets.py
  │   │       │   ├── services/
  │   │       │   │   ├── __init__.py
  │   │       │   │   ├── attendance_service.py
  │   │       │   │   └── student_service.py
  │   │       │   ├── __init__.py
  │   │       │   ├── config.py
  │   │       │   ├── customtkinter.py
  │   │       │   ├── main.py
  │   │       │   └── settings_store.py
  │   │       ├── README.md
  │   │       ├── run_qt_gui.bat
  │   │       └── run_qt_gui.py
  │   └── README.md
  ├── assets/
  │   └── icon/
  │       ├── DSIS_LOGO.ico
  │       ├── DSIS_LOGO.png
  │       └── dsis-logo.html
  ├── audit/
  │   ├── FORENSIC_AUDIT.md
  │   ├── generate_metrics.py
  │   └── source_line_counts.csv
  ├── Build/
  │   ├── DSIS_v1.spec
  │   ├── DSIS_v2.spec
  │   └── DSIS_v3.spec
  ├── docs/
  │   ├── _inbox/
  │   │   └── README.md
  │   ├── API/
  │   │   └── README.md
  │   ├── Architecture/
  │   │   ├── architecture.md
  │   │   ├── complete-system-architecture.md
  │   │   ├── data-and-settings.md
  │   │   ├── database-schema.md
  │   │   ├── pywebview-bridge-api-reference.md
  │   │   ├── pywebview-bridge.md
  │   │   ├── README.md
  │   │   ├── runtime-contract.md
  │   │   ├── software-flow.md
  │   │   ├── system-architecture.md
  │   │   ├── v3-system-architecture-detail.md
  │   │   ├── v3-system-architecture.md
  │   │   └── v3-system.md
  │   ├── Development/
  │   │   ├── change-log.md
  │   │   ├── database-integration-summary.md
  │   │   ├── database-updates.md
  │   │   ├── documentation-authority.md
  │   │   ├── documentation-manifest.md
  │   │   ├── documentation-map.md
  │   │   ├── ESP32_Fingerprint_AllInOne_firmware_explanation.md
  │   │   ├── FILES_DETAILED.md
  │   │   ├── FILES_OVERVIEW.md
  │   │   ├── implementation-summary.md
  │   │   ├── logger_usage.md
  │   │   ├── logging-guide.md
  │   │   ├── logging-quick-reference.md
  │   │   ├── logging-summary.md
  │   │   ├── logging.md
  │   │   ├── migration-example.md
  │   │   ├── polish-phase-complete.md
  │   │   ├── polish-phase-roadmap.md
  │   │   ├── PORTABLE_PYTHON.md
  │   │   ├── README.md
  │   │   ├── release-and-portable-build.md
  │   │   ├── runtime-data.md
  │   │   ├── setup.md
  │   │   ├── SHUTDOWN_CRASH.md
  │   │   ├── structure.txt
  │   │   ├── testing.md
  │   │   ├── todo.md
  │   │   ├── tools-catalog.md
  │   │   └── ui-prototypes.md
  │   ├── Dup/
  │   │   └── README.md
  │   ├── generated/
  │   │   ├── APP_INVENTORY_UI_MAP.md
  │   │   ├── APP_INVENTORY.md
  │   │   ├── ARCHITECTURE.md
  │   │   ├── DATABASE.md
  │   │   ├── FILE_INVENTORY.md
  │   │   ├── FIRMWARE.md
  │   │   ├── GUI.md
  │   │   ├── INDEX.md
  │   │   ├── PROJECT_ARCHITECTURE_TREE.md
  │   │   ├── PROJECT_ARCHITECTURE_VISUAL_TREE.md
  │   │   ├── PROJECT_FORENSIC_AUDIT.md
  │   │   ├── PROJECT_OVERVIEW.md
  │   │   ├── README.md
  │   │   ├── REPOSITORY_AUDIT.md
  │   │   ├── SERIAL_PROTOCOL.md
  │   │   └── TESTING.md
  │   ├── Hardware/
  │   │   ├── images/
  │   │   │   ├── IMG20260630233940.jpg
  │   │   │   ├── IMG20260630233946.jpg
  │   │   │   ├── IMG20260630233949.jpg
  │   │   │   ├── IMG20260630235111.jpg
  │   │   │   ├── IMG20260630235113.jpg
  │   │   │   ├── IMG20260630235115.jpg
  │   │   │   ├── IMG20260630235122.jpg
  │   │   │   ├── IMG20260630235124.jpg
  │   │   │   ├── IMG20260630235318.jpg
  │   │   │   ├── IMG20260701000304.jpg
  │   │   │   ├── IMG20260701000309.jpg
  │   │   │   ├── IMG20260701000315.jpg
  │   │   │   ├── IMG20260701000319.jpg
  │   │   │   ├── IMG20260701000326.jpg
  │   │   │   ├── IMG20260701000328.jpg
  │   │   │   ├── IMG20260701010721.jpg
  │   │   │   ├── IMG20260701010726.jpg
  │   │   │   └── IMG20260701010735.jpg
  │   │   ├── drivers-and-ports.md
  │   │   ├── firmware-variants.md
  │   │   ├── firmware.md
  │   │   ├── hardware-connections.md
  │   │   ├── README.md
  │   │   ├── serial-protocol.md
  │   │   └── wiring.md
  │   ├── History/
  │   │   ├── README.md
  │   │   └── ui-lineage.md
  │   ├── Overview/
  │   │   ├── project-overview.md
  │   │   └── version-history.md
  │   ├── Research/
  │   │   ├── DSIS_CONCEPT_PAPER_SOURCE_NOTES.md
  │   │   └── DSIS_CONCEPT_PAPER.md
  │   ├── Security/
  │   │   └── security-model.md
  │   ├── Troubleshooting/
  │   │   ├── database.md
  │   │   ├── desktop.md
  │   │   ├── README.md
  │   │   └── serial-and-device.md
  │   ├── UserGuide/
  │   │   ├── images/
  │   │   │   ├── 151746.png
  │   │   │   ├── 151826.png
  │   │   │   ├── qt-ui-2026-08-12-234248.png
  │   │   │   ├── qt-ui-2026-08-12-234601.png
  │   │   │   ├── qt-ui-2026-08-13-003704.png
  │   │   │   ├── qt-ui-2026-08-13-004222.png
  │   │   │   ├── qt-ui-2026-08-13-005414.png
  │   │   │   ├── qt-ui-2026-08-13-010056.png
  │   │   │   ├── qt-ui-2026-08-13-013942.png
  │   │   │   ├── qt-ui-2026-08-13-014047.png
  │   │   │   ├── qt-ui-2026-08-13-014333.png
  │   │   │   ├── qt-ui-2026-08-13-014828.png
  │   │   │   ├── qt-ui-2026-08-13-015151.png
  │   │   │   ├── qt-ui-2026-08-13-015535.png
  │   │   │   ├── qt-ui-2026-08-13-023656.png
  │   │   │   ├── qt-ui-2026-08-13-024251.png
  │   │   │   ├── qt-ui-2026-08-13-152422.png
  │   │   │   ├── qt-ui-2026-08-13-152935.png
  │   │   │   ├── qt-ui-2026-08-13-153334.png
  │   │   │   ├── qt-ui-2026-08-13-153458.png
  │   │   │   ├── qt-ui-2026-08-13-155508.png
  │   │   │   ├── qt-ui-2026-08-13-160601.png
  │   │   │   ├── qt-ui-2026-08-13-174028.png
  │   │   │   ├── qt-ui-2026-08-13-183526.png
  │   │   │   ├── qt-ui-2026-08-13-183539.png
  │   │   │   ├── qt-ui-2026-08-13-184406.png
  │   │   │   ├── qt-ui-2026-08-13-185046.png
  │   │   │   ├── qt-ui-2026-08-13-194258.png
  │   │   │   ├── qt-ui-2026-08-13-200344.png
  │   │   │   ├── qt-ui-2026-08-13-201746.png
  │   │   │   ├── qt-ui-2026-08-14-130125.png
  │   │   │   ├── qt-ui-2026-08-14-130718.png
  │   │   │   ├── qt-ui-2026-08-14-170026.png
  │   │   │   ├── qt-ui-2026-08-14-170031.png
  │   │   │   ├── qt-ui-2026-08-14-171112.png
  │   │   │   ├── qt-ui-2026-08-14-172424.png
  │   │   │   ├── qt-ui-2026-08-14-172719.png
  │   │   │   ├── qt-ui-2026-08-14-174120.png
  │   │   │   ├── qt-ui-2026-08-14-174357.png
  │   │   │   ├── qt-ui-2026-08-14-192838.png
  │   │   │   ├── qt-ui-2026-08-14-193007.png
  │   │   │   ├── qt-ui-2026-08-14-193047.png
  │   │   │   ├── qt-ui-2026-08-14-193827.png
  │   │   │   ├── qt-ui-2026-08-14-193919.png
  │   │   │   ├── qt-ui-2026-08-14-211342.png
  │   │   │   ├── qt-ui-2026-08-14-211411.png
  │   │   │   ├── qt-ui-2026-08-14-211419.png
  │   │   │   ├── qt-ui-2026-08-14-211425.png
  │   │   │   ├── qt-ui-2026-08-14-211443.png
  │   │   │   ├── qt-ui-2026-08-14-211453.png
  │   │   │   ├── qt-ui-2026-08-16-213817.png
  │   │   │   ├── qt-ui-2026-08-16-214003.png
  │   │   │   ├── qt-ui-2026-08-16-214859.png
  │   │   │   ├── qt-ui-2026-08-16-215140.png
  │   │   │   ├── qt-ui-2026-08-16-215420.png
  │   │   │   ├── qt-ui-2026-08-16-220007.png
  │   │   │   ├── qt-ui-2026-08-16-220802.png
  │   │   │   ├── qt-ui-2026-08-16-220859.png
  │   │   │   ├── qt-ui-2026-08-17-164332.png
  │   │   │   ├── qt-ui-2026-08-17-185720.png
  │   │   │   ├── qt-ui-2026-08-17-185752.png
  │   │   │   ├── qt-ui-2026-08-18-115635.png
  │   │   │   ├── qt-ui-2026-08-18-115700.png
  │   │   │   ├── qt-ui-2026-08-18-115744.png
  │   │   │   ├── qt-ui-2026-08-18-115810.png
  │   │   │   ├── qt-ui-2026-08-18-160724.png
  │   │   │   ├── qt-ui-2026-08-27-102017.png
  │   │   │   ├── qt-ui-2026-08-27-231106.png
  │   │   │   ├── qt-ui-2026-08-27-231147.png
  │   │   │   ├── qt-ui-2026-08-27-231205.png
  │   │   │   ├── qt-ui-2026-08-27-234622.png
  │   │   │   ├── qt-ui-2026-08-27-235125.png
  │   │   │   ├── qt-ui-2026-08-27-235358.png
  │   │   │   ├── qt-ui-2026-08-27-235856.png
  │   │   │   ├── qt-ui-2026-08-28-000016.png
  │   │   │   ├── qt-ui-2026-08-28-000024.png
  │   │   │   ├── qt-ui-2026-08-28-000035.png
  │   │   │   ├── qt-ui-2026-08-28-000051.png
  │   │   │   ├── qt-ui-2026-08-28-000059.png
  │   │   │   ├── qt-ui-2026-08-28-000114.png
  │   │   │   ├── qt-ui-2026-08-28-000119.png
  │   │   │   ├── qt-ui-2026-08-28-000125.png
  │   │   │   ├── qt-ui-2026-08-28-001903.png
  │   │   │   ├── Screenshot 2026-06-27 182256.png
  │   │   │   ├── Screenshot 2026-06-29 232644.png
  │   │   │   ├── Screenshot 2026-06-29 233641.png
  │   │   │   ├── Screenshot 2026-06-30 115359.png
  │   │   │   ├── Screenshot 2026-06-30 115404.png
  │   │   │   ├── Screenshot 2026-06-30 190312.png
  │   │   │   ├── Screenshot 2026-06-30 193423.png
  │   │   │   ├── Screenshot 2026-06-30 193928.png
  │   │   │   ├── Screenshot 2026-06-30 194343.png
  │   │   │   ├── Screenshot 2026-06-30 194530.png
  │   │   │   ├── Screenshot 2026-06-30 195210.png
  │   │   │   ├── Screenshot 2026-06-30 200710.png
  │   │   │   ├── Screenshot 2026-06-30 201634.png
  │   │   │   ├── Screenshot 2026-06-30 204935.png
  │   │   │   ├── Screenshot 2026-06-30 205811.png
  │   │   │   ├── Screenshot 2026-06-30 205826.png
  │   │   │   ├── Screenshot 2026-06-30 212105.png
  │   │   │   ├── Screenshot 2026-06-30 213207.png
  │   │   │   ├── Screenshot 2026-06-30 214250.png
  │   │   │   ├── Screenshot 2026-06-30 223351.png
  │   │   │   ├── Screenshot 2026-06-30 230553.png
  │   │   │   ├── Screenshot 2026-06-30 230614.png
  │   │   │   ├── Screenshot 2026-06-30 231636.png
  │   │   │   ├── Screenshot 2026-06-30 234700.png
  │   │   │   ├── Screenshot 2026-07-01 215932.png
  │   │   │   ├── Screenshot 2026-07-01 220522.png
  │   │   │   ├── Screenshot 2026-07-01 220725.png
  │   │   │   ├── Screenshot 2026-07-01 222527.png
  │   │   │   ├── Screenshot 2026-07-01 222624.png
  │   │   │   ├── Screenshot 2026-07-01 223020.png
  │   │   │   ├── Screenshot 2026-07-02 000130.png
  │   │   │   ├── Screenshot 2026-07-02 213944.png
  │   │   │   ├── Screenshot 2026-07-02 215347.png
  │   │   │   ├── Screenshot 2026-07-02 215354.png
  │   │   │   ├── Screenshot 2026-07-03 122804.png
  │   │   │   ├── Screenshot 2026-07-04 010505.png
  │   │   │   ├── Screenshot 2026-07-04 025719.png
  │   │   │   ├── Screenshot 2026-07-04 025743.png
  │   │   │   ├── Screenshot 2026-07-04 025834.png
  │   │   │   ├── Screenshot 2026-07-04 030024.png
  │   │   │   ├── Screenshot 2026-07-04 030032.png
  │   │   │   ├── Screenshot 2026-07-04 030115.png
  │   │   │   ├── Screenshot 2026-07-04 031323.png
  │   │   │   ├── Screenshot 2026-07-04 031534.png
  │   │   │   ├── Screenshot 2026-07-04 035208.png
  │   │   │   ├── Screenshot 2026-07-04 221654.png
  │   │   │   ├── Screenshot 2026-07-04 221905.png
  │   │   │   ├── Screenshot 2026-07-04 222938.png
  │   │   │   ├── Screenshot 2026-07-04 230533.png
  │   │   │   ├── Screenshot 2026-07-05 172750.png
  │   │   │   ├── Screenshot 2026-07-05 172808.png
  │   │   │   ├── Screenshot 2026-07-05 172824.png
  │   │   │   ├── Screenshot 2026-07-05 181406.png
  │   │   │   ├── Screenshot 2026-07-05 181409.png
  │   │   │   ├── Screenshot 2026-07-05 181414.png
  │   │   │   ├── Screenshot 2026-07-05 182045.png
  │   │   │   ├── Screenshot 2026-07-05 191105.png
  │   │   │   ├── Screenshot 2026-07-05 201039.png
  │   │   │   ├── Screenshot 2026-07-06 215013.png
  │   │   │   ├── Screenshot 2026-07-06 220200.png
  │   │   │   ├── Screenshot 2026-07-06 220415.png
  │   │   │   ├── Screenshot 2026-07-06 220426.png
  │   │   │   ├── Screenshot 2026-08-28 014724.png
  │   │   │   ├── Screenshot 2026-08-28 015319.png
  │   │   │   ├── Screenshot 2026-08-28 020245.png
  │   │   │   ├── Screenshot 2026-09-02 234821.png
  │   │   │   ├── Screenshot 2026-09-03 105641.png
  │   │   │   ├── Screenshot 2026-09-03 105836.png
  │   │   │   ├── Screenshot 2026-09-03 105843.png
  │   │   │   ├── Screenshot 2026-09-03 105848.png
  │   │   │   ├── Screenshot 2026-09-03 110300.png
  │   │   │   ├── Screenshot 2026-09-03 110927.png
  │   │   │   ├── Screenshot 2026-09-03 111317.png
  │   │   │   ├── Screenshot 2026-09-03 111403.png
  │   │   │   ├── Screenshot 2026-09-03 111715.png
  │   │   │   ├── Screenshot 2026-09-03 112101.png
  │   │   │   ├── Screenshot 2026-09-03 112351.png
  │   │   │   ├── Screenshot 2026-09-03 112652.png
  │   │   │   ├── Screenshot 2026-09-03 113630.png
  │   │   │   ├── Screenshot 2026-09-03 114240.png
  │   │   │   ├── Screenshot 2026-09-03 114303.png
  │   │   │   ├── Screenshot 2026-09-03 120126.png
  │   │   │   ├── Screenshot 2026-09-03 120151.png
  │   │   │   ├── Screenshot 2026-09-03 120158.png
  │   │   │   ├── Screenshot 2026-09-04 140823.png
  │   │   │   ├── Screenshot 2026-09-04 202622.png
  │   │   │   ├── Screenshot 2026-09-04 202629.png
  │   │   │   ├── Screenshot 2026-09-04 202635.png
  │   │   │   ├── Screenshot 2026-09-04 202639.png
  │   │   │   ├── Screenshot 2026-09-04 202644.png
  │   │   │   ├── Screenshot 2026-09-04 202649.png
  │   │   │   ├── Screenshot 2026-09-04 202835.png
  │   │   │   ├── Screenshot 2026-09-04 202842.png
  │   │   │   ├── Screenshot 2026-09-04 202859.png
  │   │   │   ├── Screenshot 2026-09-04 202904.png
  │   │   │   ├── Screenshot 2026-09-04 202909.png
  │   │   │   ├── Screenshot 2026-09-04 202914.png
  │   │   │   ├── Screenshot 2026-09-06 193100.png
  │   │   │   ├── Screenshot 2026-09-06 194952.png
  │   │   │   ├── Screenshot 2026-09-06 195634.png
  │   │   │   ├── Screenshot 2026-09-06 200000.png
  │   │   │   ├── Screenshot 2026-09-06 200350.png
  │   │   │   ├── Screenshot 2026-09-06 200442.png
  │   │   │   ├── Screenshot 2026-09-06 200624.png
  │   │   │   ├── Screenshot 2026-09-06 201100.png
  │   │   │   ├── Screenshot 2026-09-06 201239.png
  │   │   │   ├── Screenshot 2026-09-06 201249.png
  │   │   │   ├── Screenshot 2026-09-06 201257.png
  │   │   │   ├── Screenshot 2026-09-06 232754.png
  │   │   │   ├── Screenshot 2026-09-06 232824.png
  │   │   │   ├── Screenshot 2026-09-07 010626.png
  │   │   │   ├── Screenshot 2026-09-07 120536.png
  │   │   │   ├── Screenshot 2026-09-07 120743.png
  │   │   │   ├── Screenshot 2026-09-07 120816.png
  │   │   │   ├── Screenshot 2026-09-07 121122.png
  │   │   │   ├── Screenshot 2026-09-07 121349.png
  │   │   │   ├── Screenshot 2026-09-07 121558.png
  │   │   │   ├── Screenshot 2026-09-07 121609.png
  │   │   │   ├── Screenshot 2026-09-07 122203.png
  │   │   │   ├── Screenshot 2026-09-07 122216.png
  │   │   │   ├── Screenshot 2026-09-07 122317.png
  │   │   │   ├── Screenshot 2026-09-09 150815.png
  │   │   │   ├── Screenshot 2026-09-09 154521.png
  │   │   │   ├── Screenshot 2026-09-09 154741.png
  │   │   │   ├── Screenshot 2026-09-09 161200.png
  │   │   │   ├── Screenshot 2026-09-09 161205.png
  │   │   │   ├── Screenshot 2026-09-09 174846.png
  │   │   │   ├── Screenshot 2026-09-10 003322.png
  │   │   │   ├── Screenshot 2026-09-10 180330.png
  │   │   │   ├── Screenshot 2026-09-10 180508.png
  │   │   │   ├── Screenshot 2026-09-10 183846.png
  │   │   │   ├── Screenshot 2026-09-10 185944.png
  │   │   │   ├── Screenshot 2026-09-10 190014.png
  │   │   │   ├── Screenshot 2026-09-10 190024.png
  │   │   │   ├── Screenshot 2026-09-10 190033.png
  │   │   │   ├── Screenshot 2026-09-10 190045.png
  │   │   │   ├── Screenshot 2026-09-10 190054.png
  │   │   │   ├── Screenshot 2026-09-10 201338.png
  │   │   │   ├── Screenshot 2026-09-10 222518.png
  │   │   │   ├── Screenshot 2026-09-11 000534.png
  │   │   │   ├── Screenshot 2026-09-11 001513.png
  │   │   │   ├── Screenshot 2026-09-11 001542.png
  │   │   │   ├── Screenshot 2026-09-11 004426.png
  │   │   │   ├── Screenshot 2026-09-11 004538.png
  │   │   │   ├── Screenshot 2026-09-11 005210.png
  │   │   │   ├── Screenshot 2026-09-11 005555.png
  │   │   │   ├── Screenshot 2026-09-11 005844.png
  │   │   │   ├── Screenshot 2026-09-11 005929.png
  │   │   │   ├── Screenshot 2026-09-11 010253.png
  │   │   │   ├── Screenshot 2026-09-11 010453.png
  │   │   │   ├── Screenshot 2026-09-11 010458.png
  │   │   │   ├── Screenshot 2026-09-11 010503.png
  │   │   │   ├── Screenshot 2026-09-11 011919.png
  │   │   │   ├── Screenshot 2026-09-11 012403.png
  │   │   │   ├── Screenshot 2026-09-11 012521.png
  │   │   │   ├── Screenshot 2026-09-11 013546.png
  │   │   │   ├── Screenshot 2026-09-11 014255.png
  │   │   │   ├── Screenshot 2026-09-11 014305.png
  │   │   │   ├── Screenshot 2026-09-11 014608.png
  │   │   │   ├── Screenshot 2026-09-11 014713.png
  │   │   │   ├── Screenshot 2026-09-11 015116.png
  │   │   │   ├── Screenshot 2026-09-11 162739.png
  │   │   │   ├── Screenshot 2026-09-11 162819.png
  │   │   │   ├── Screenshot 2026-09-11 165720.png
  │   │   │   ├── Screenshot 2026-09-11 165737.png
  │   │   │   ├── Screenshot 2026-09-11 165747.png
  │   │   │   ├── Screenshot 2026-09-11 165801.png
  │   │   │   ├── Screenshot 2026-09-11 170027.png
  │   │   │   ├── Screenshot 2026-09-11 170040.png
  │   │   │   ├── Screenshot 2026-09-11 170048.png
  │   │   │   ├── Screenshot 2026-09-11 170249.png
  │   │   │   ├── Screenshot 2026-09-15 233618.png
  │   │   │   ├── Screenshot 2026-09-15 235047.png
  │   │   │   ├── Screenshot 2026-09-16 104620.png
  │   │   │   ├── Screenshot 2026-09-17 221421.png
  │   │   │   ├── Screenshot 2026-09-17 222009.png
  │   │   │   ├── Screenshot 2026-09-17 225002.png
  │   │   │   ├── Screenshot 2026-09-17 225011.png
  │   │   │   ├── Screenshot 2026-09-17 225448.png
  │   │   │   ├── Screenshot 2026-09-17 225455.png
  │   │   │   ├── Screenshot 2026-09-17 230340.png
  │   │   │   ├── Screenshot 2026-09-17 230610.png
  │   │   │   ├── Screenshot 2026-09-17 233547.png
  │   │   │   ├── Screenshot 2026-09-17 234141.png
  │   │   │   ├── Screenshot 2026-09-17 234158.png
  │   │   │   ├── Screenshot 2026-09-17 234212.png
  │   │   │   ├── Screenshot 2026-09-18 005509.png
  │   │   │   ├── Screenshot 2026-09-18 112230.png
  │   │   │   ├── Screenshot 2026-09-18 113755.png
  │   │   │   ├── Screenshot 2026-09-19 214428.png
  │   │   │   ├── Screenshot 2026-09-19 214504.png
  │   │   │   ├── Screenshot 2026-09-19 214626.png
  │   │   │   ├── Screenshot 2026-09-19 214718.png
  │   │   │   ├── Screenshot 2026-09-19 221224.png
  │   │   │   ├── Screenshot 2026-09-19 221311.png
  │   │   │   ├── Screenshot 2026-09-19 222615.png
  │   │   │   ├── Screenshot 2026-09-20 022255.png
  │   │   │   ├── Screenshot 2026-09-20 022258.png
  │   │   │   ├── Screenshot 2026-09-20 022325.png
  │   │   │   ├── Screenshot 2026-09-20 022342.png
  │   │   │   ├── Screenshot 2026-09-20 022559.png
  │   │   │   ├── Screenshot 2026-09-20 022610.png
  │   │   │   ├── Screenshot 2026-09-20 022620.png
  │   │   │   ├── Screenshot 2026-09-20 022638.png
  │   │   │   ├── Screenshot 2026-09-20 023047.png
  │   │   │   ├── Screenshot 2026-09-20 023518.png
  │   │   │   ├── Screenshot 2026-09-20 023559.png
  │   │   │   ├── Screenshot 2026-09-20 023807.png
  │   │   │   ├── Screenshot 2026-09-20 023811.png
  │   │   │   ├── Screenshot 2026-09-20 023814.png
  │   │   │   ├── Screenshot 2026-09-20 145823.png
  │   │   │   ├── Screenshot 2026-09-20 150125.png
  │   │   │   ├── Screenshot 2026-09-20 151051.png
  │   │   │   ├── Screenshot 2026-09-20 151106.png
  │   │   │   ├── Screenshot 2026-09-20 151118.png
  │   │   │   ├── Screenshot 2026-09-20 151128.png
  │   │   │   ├── Screenshot 2026-09-20 151141.png
  │   │   │   ├── Screenshot 2026-09-20 151746.png
  │   │   │   ├── Screenshot 2026-09-20 151758.png
  │   │   │   ├── Screenshot 2026-09-20 151807.png
  │   │   │   ├── Screenshot 2026-09-20 151815.png
  │   │   │   ├── Screenshot 2026-09-20 151826.png
  │   │   │   ├── Screenshot 2026-09-20 151849.png
  │   │   │   ├── Screenshot_2026-08-28_014145.png
  │   │   │   └── Screenshot_2026-08-28_014206.png
  │   │   ├── attendance-rules.md
  │   │   ├── backup-restore-export.md
  │   │   ├── enrollment-and-scanning.md
  │   │   ├── first-run-wizard.md
  │   │   ├── installation-guide.md
  │   │   ├── project-overview.md
  │   │   ├── README.md
  │   │   ├── roles-and-permissions.md
  │   │   ├── testing-results.md
  │   │   ├── v3-workflows.md
  │   │   └── workflows.md
  │   ├── audit_file_inventory.csv
  │   ├── CODE_METRICS.csv
  │   ├── CODE_METRICS.md
  │   ├── Documentation-Inventory.md
  │   ├── Documentation-Overhaul.md
  │   ├── dsis_prototype.html
  │   ├── ENROLLMENT_REGRESSION_DIAGNOSTIC.md
  │   ├── INDEX.md
  │   ├── notes.txt
  │   ├── README.md
  │   ├── REGRESSION_INVESTIGATION_SUMMARY.md
  │   ├── ROOT_CAUSE_ANALYSIS.md
  │   ├── Screenshot 2026-09-17 233547.png
  │   ├── SECURITY_AUDIT_REPORT.md
  │   ├── SECURITY_REMEDIATION_REPORT.md
  │   └── TROUBLESHOOTING.md
  ├── driver/
  │   └── Install_CP210x_Driver.bat
  ├── firmware/
  │   ├── attendance/
  │   │   └── attendance.ino
  │   ├── delete/
  │   │   └── delete.ino
  │   ├── enroll/
  │   │   └── enroll.ino
  │   ├── ESP32_DSIS_AllInOne/
  │   │   ├── src/
  │   │   │   └── rfid/
  │   │   │       ├── CardDetector.cpp
  │   │   │       ├── CardDetector.h
  │   │   │       ├── ClassicAdapter.cpp
  │   │   │       ├── ClassicAdapter.h
  │   │   │       ├── Type2Adapter.cpp
  │   │   │       └── Type2Adapter.h
  │   │   └── ESP32_DSIS_AllInOne.ino
  │   ├── ESP32_Fingerprint_AllInOne/
  │   │   └── ESP32_Fingerprint_AllInOne.ino
  │   ├── rc522_dumpinfo_test/
  │   │   └── rc522_dumpinfo_test.ino
  │   ├── rc522_read/
  │   │   └── rc522_read.ino
  │   ├── rc522_readwrite/
  │   │   └── rc522_readwrite.ino
  │   ├── rc522_test/
  │   │   └── rc522_test.ino
  │   ├── rc522_write/
  │   │   └── rc522_write.ino
  │   └── test/
  │       └── fingerprint_check/
  │           └── fingerprint_check.ino
  ├── python/
  │   ├── core/
  │   │   ├── __init__.py
  │   │   ├── attendance_calendar.py
  │   │   ├── attendance_status.py
  │   │   ├── attendance.py
  │   │   ├── auth.py
  │   │   ├── commands.py
  │   │   ├── database.py
  │   │   ├── device_discovery.py
  │   │   ├── firmware_helper.py
  │   │   ├── logger.py
  │   │   ├── permissions.py
  │   │   ├── rfid_card.py
  │   │   ├── serial_handler.py
  │   │   ├── setup_wizard.py
  │   │   └── utils.py
  │   ├── gui/
  │   │   ├── legacy/
  │   │   │   ├── bfeas_app2.py
  │   │   │   └── reports_table_page.py
  │   │   └── __init__.py
  │   ├── gui_qt/
  │   │   └── __init__.py
  │   ├── gui_web/
  │   │   ├── v2_reference/
  │   │   │   ├── gui_qt/
  │   │   │   │   ├── pages/
  │   │   │   │   │   ├── __init__.py
  │   │   │   │   │   ├── attendance_page.py
  │   │   │   │   │   ├── dashboard_page.py
  │   │   │   │   │   ├── logs_page.py
  │   │   │   │   │   ├── reports_page.py
  │   │   │   │   │   ├── settings_page.py
  │   │   │   │   │   └── students_page.py
  │   │   │   │   ├── widgets/
  │   │   │   │   │   ├── __init__.py
  │   │   │   │   │   ├── sidebar.py
  │   │   │   │   │   └── stat_card.py
  │   │   │   │   ├── workers/
  │   │   │   │   │   ├── __init__.py
  │   │   │   │   │   ├── connection_worker.py
  │   │   │   │   │   └── serial_worker.py
  │   │   │   │   ├── __init__.py
  │   │   │   │   ├── main_qt.py
  │   │   │   │   ├── main_window.py
  │   │   │   │   ├── theme_light.qss
  │   │   │   │   └── theme.qss
  │   │   │   └── README.md
  │   │   ├── web/
  │   │   │   ├── app.js
  │   │   │   ├── index.html
  │   │   │   └── styles.css
  │   │   ├── __init__.py
  │   │   ├── api.py
  │   │   ├── main_web.py
  │   │   └── perf_profiler.py
  │   ├── services/
  │   │   ├── __init__.py
  │   │   ├── attendance_service.py
  │   │   └── student_service.py
  │   ├── __init__.py
  │   ├── config.py
  │   ├── main.py
  │   └── settings_store.py
  ├── system/
  │   └── python/
  │       └── README.md
  ├── tests/
  │   ├── _archives/
  │   │   ├── ESP32 R307 Finger print Sensor/
  │   │   │   ├── ESP32_enroll_R307_finger_Print/
  │   │   │   │   └── ESP32_enroll_R307_finger_Print.ino
  │   │   │   └── esp32_fingerprint_check_R307/
  │   │   │       └── esp32_fingerprint_check_R307.ino
  │   │   ├── ESP32 R307 Finger print Sensor.zip
  │   │   ├── gui_qt_redesign.zip
  │   │   └── qt_gui_interactive_bundle.zip
  │   ├── _reference/
  │   │   ├── ENHANCED_GUI_GUIDE.txt
  │   │   ├── HOW_TO_RUN_TEST_GUI.txt
  │   │   ├── QUICK_REFERENCE.txt
  │   │   ├── README_QT_GUI_TEST.md
  │   │   ├── README_TEST_GUI.txt
  │   │   ├── run_qt_gui_test.bat
  │   │   ├── TEST_GUI_README.md
  │   │   └── VISUAL_GUIDE.txt
  │   ├── legacy/
  │   │   ├── raw_serial_diagnostic/
  │   │   │   └── raw_serial_diagnostic.ino
  │   │   ├── phase2_databasev1.py
  │   │   ├── phase2_databasev2.py
  │   │   ├── phase2_databasev3.py
  │   │   ├── phase2_databasev4.py
  │   │   └── phase2_serial_test.py
  │   ├── manual_hardware_scripts/
  │   │   ├── test_debug_raw_lines.py
  │   │   ├── test_enrollment_with_worker.py
  │   │   ├── test_gui_demo.py
  │   │   └── test_minimal_enroll.py
  │   ├── Prototype/
  │   │   ├── Python/
  │   │   │   ├── actual_ui_prototype.py
  │   │   │   ├── combined_ui.py
  │   │   │   ├── hybrid_window.py
  │   │   │   ├── original_window.py
  │   │   │   ├── prototype_window.py
  │   │   │   └── task_manager_window.py
  │   │   ├── tests/
  │   │   │   ├── test_actual_ui_prototype.py
  │   │   │   ├── test_combined_ui.py
  │   │   │   ├── test_hybrid_prototype.py
  │   │   │   ├── test_original_ui.py
  │   │   │   ├── test_qt_prototype.py
  │   │   │   └── test_task_manager_variant.py
  │   │   ├── hybrid_window.py
  │   │   ├── original_ui.py
  │   │   ├── run_combined_ui.py
  │   │   ├── run_hybrid_prototype.py
  │   │   ├── run_original_ui_display.py
  │   │   ├── run_qt_prototype.py
  │   │   └── run_task_manager_variant.py
  │   ├── app_test.py
  │   ├── comprehensive_test.py
  │   ├── conftest.py
  │   ├── physical_esp32_smoke.py
  │   ├── qt_gui_interactive.py
  │   ├── test_active_firmware_protocol.py
  │   ├── test_attendance_export_rows.py
  │   ├── test_attendance_parsing.py
  │   ├── test_attendance_processor.py
  │   ├── test_attendance_refresh.py
  │   ├── test_attendance_status.py
  │   ├── test_attendance_ui_regressions.py
  │   ├── test_attendance_ui_utils.py
  │   ├── test_auto_port_probe.py
  │   ├── test_bfeas_app2_import.py
  │   ├── test_button_in_context.py
  │   ├── test_database_features.py
  │   ├── test_database_reset.py
  │   ├── test_database_security.py
  │   ├── test_dialog_enrollment_integration.py
  │   ├── test_dialog_handlers.py
  │   ├── test_enrollment_debug.py
  │   ├── test_enrollment_dialog_ux.py
  │   ├── test_error_message_sanitization.py
  │   ├── test_firmware_helper.py
  │   ├── test_gui_settings_integration.py
  │   ├── test_gui_shutdown.py
  │   ├── test_gui_web_smoke.py
  │   ├── test_mode_exclusivity.py
  │   ├── test_permissions_and_attendance_tagging.py
  │   ├── test_project_structure.py
  │   ├── test_qt_attendance_page.py
  │   ├── test_qt_enrollment_flow.py
  │   ├── test_qt_main_window.py
  │   ├── test_qt_serial_worker.py
  │   ├── test_qt_settings_logs.py
  │   ├── test_qt_shell.py
  │   ├── test_qt_students_page.py
  │   ├── test_qt_thread_exception_handling.py
  │   ├── test_reports_page_import.py
  │   ├── test_responsive_layout.py
  │   ├── test_sensor_failure_handshake_recovery.py
  │   ├── test_serial_handler_host_gate.py
  │   ├── test_serial_monitor_boot_banner.py
  │   ├── test_serial_troubleshooting.py
  │   ├── test_settings_persistence.py
  │   ├── test_settings_toggles.py
  │   ├── test_student_input_regression.py
  │   ├── test_student_input_validation.py
  │   ├── test_theme_switching.py
  │   ├── test_type_hints.py
  │   ├── test_v3_authentication.py
  │   ├── test_vidpid_normalization.py
  │   ├── tmp_card_claim_test.db
  │   └── whs_dashboard.py
  ├── tools/
  │   ├── _database_refactor.py
  │   ├── archive_unused_python.py
  │   ├── copilot_forensic_search.py
  │   ├── debug_db_connections.py
  │   ├── fingerprint_portable.spec
  │   ├── list_files.bat
  │   ├── runtime_manager.py
  │   ├── serial_handler_connect_probe.py
  │   ├── serial_pipeline_tester.py
  │   ├── serial_worker_probe.py
  │   └── verify_gui_startup.py
  ├── .gitattributes
  ├── .gitignore
  ├── CODE_OF_CONDUCT.md
  ├── CONTRIBUTING.md
  ├── install_requirements.bat
  ├── INSTALLATION.md
  ├── LICENSE
  ├── PORTABLE_BUILD.md
  ├── pytest.ini
  ├── README.md
  ├── RELEASE.md
  ├── requirements.txt
  ├── run_web_gui.bat
  ├── run_web_gui.py
  └── SECURITY.md
```

## Companion exact source map

- [Full Project Architecture Tree & Symbol Map](PROJECT_ARCHITECTURE_TREE.md) — exact current repository tree plus source-level symbols.
- [Complete DSIS System Architecture](../Architecture/complete-system-architecture.md) — narrative architecture, boundaries, flows, and lineage.
