# DSIS Project Architecture — Visual Family Tree

> A visual, branch-style architecture map of the entire DSIS project.
>
> This is intentionally presented as a **family tree / system tree**, not a normal folder listing.
>
> **Current maintained runtime:** V3 HTML + JavaScript + pywebview + Python + SQLite + ESP32 All-In-One firmware.
>
> **Historical branches:** V1, V2, legacy UI, diagnostics, prototypes, and archived implementations remain separate from the current runtime.

\`\`\`text
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

\`\`\`

## Reading rule

This tree describes the **relationship between parts**, not merely where files happen to live.

A file can belong to a subsystem while its functions participate in a different runtime path. The arrows therefore describe architectural responsibility and data/control flow, while the file names identify the implementation locations.

For exact source inventories, use the companion generated project tree and application inventory.
