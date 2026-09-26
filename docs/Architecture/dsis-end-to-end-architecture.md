# DSIS End-to-End Architecture Overview

This document consolidates the project’s end-to-end system architecture into a single Markdown reference. It captures the full flow from the user interface, through the Python backend, into hardware interaction, device protocol processing, persistence, and reporting.

> Scope: current maintained DSIS runtime; architecture is aligned with the project’s canonical architecture references and the active v3 web UI flow.

```text
╔══════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                        DIGITAL STUDENT IDENTIFICATION SYSTEM  —  DSIS                                    ║
║                        ONE GIANT CONTINUOUS PIPE  ·  TOP → BOTTOM → BACK TO TOP                          ║
║              (verified against docs/Architecture/complete-system-architecture.md, main branch)           ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════════╝
                                                    │
                                                    ▼
                                             ┌─────────────┐
                                             │    DSIS     │
                                             └──────┬──────┘
                                                    │
          ┌─────────────────────────────────────────┼─────────────────────────────────────────┐
          │                                         │                                         │
          ▼                                         ▼                                         ▼
     ┌─────────┐                              ┌───────────┐                             ┌───────────┐
     │  USER   │                              │ SOFTWARE  │                             │ HARDWARE  │
     └────┬────┘                              └─────┬─────┘                             └─────┬─────┘
          │                                         │                                         │
          │ start / connect / scan                  ▼                                         ▼
          │ enroll / manage / report          V3 DESKTOP APP                        ESP32 WROOM-32
          │                                    (run_web_gui.py /                    "DSIS All-In-One"
          │                                     run_web_gui.bat →                    firmware 1.2.5,
          │                                     gui_web.main_web)                    protocol 1
          │                                         │                                         │
          │                                         ▼                        ┌────────────────┼────────────────┐
          │                                     pywebview                     │                │                │
          │                                    NATIVE WINDOW                  USB SERIAL       UART2            SPI
          │                                         │                         115200           57600            BUS
          │                                         ▼                            │                │                │
          │                                      Web UI                         │                ▼                ▼
          │              ┌──────────────────────────┼──────────────┐          │              AS608            RC522
          │              │                          │              │          │            (fingerprint)    (RFID reader)
          │              ▼                          ▼              ▼          │                │                │
          │         index.html                 styles.css       app.js        │                │                │
          │              │                          │              │          │                │                │
          │              │ Dashboard · Attendance ·  │              │          │                │                │
          │              │ Students · Reports · Logs │              │          │                │                │
          │              │ Settings · Calendar       │              │          │                │                │
          │              │                          │              │          │                │                │
          │              └──────────────────────────┼──────────────┘          │                │                │
          │                                         │                         │                │                │
          └─────────────────────────────────────────┤                         │                │                │
                                                    ▼                         │                │                │
                                          window.pywebview.api                │                │                │
                                                    │                         │                │                │
                                                    ▼                         │                │                │
                                          python/gui_web/api.py               │                │                │
                                                    │                         │                │                │
        ┌───────────────────┬───────────────────┬───┴──────┬───────────────┬──────────────┐    │                │
        │                   │                   │          │               │              │    │                │
        ▼                   ▼                   ▼          ▼               ▼              ▼    │                │
   CONNECTION            STUDENT           IDENTIFICATION ATTENDANCE    REPORTING      CALENDAR   │                │
     OPS                  OPS                  OPS          OPS            │              │       │                │
        │                   │                   │            │            │              │       │                │
   connect             save / edit         fingerprint    scan_result   reports        holidays    │                │
   disconnect          enrollment          RFID scan      attendance    CSV prep      suspensions   │                │
   port discovery      deletion            RFID register  records      chart gen.    schedule      │                │
   reconnect                                RFID erase     evaluation                exceptions    │                │
        │                   │                   │            │            │              │       │                │
        └───────────────────┴───────────────────┴──────┬─────┴────────────┴──────────────┘       │                │
                                                        │                                          │                │
                              ┌─────────────────────────┼──────────────────────────┐                │                │
                              ▼                         ▼                          ▼                │                │
                          SETTINGS                AUTHENTICATION              LIVE UI EVENTS         │                │
                              │                         │                          │                │
                        device settings           login / password         scan_result              │                │
                        attendance rules          session state            serial_line               │                │
                        UI settings                                        log_line                  │                │
                                                                            enroll_progress            │                │
                                                                            delete_progress            │                │
                                                                            wipe_progress               │                │
                                                                            fingerprint_count            │                │
                                                                            connection_status            │                │
                                                                            data_changed                  │                │
                                                                            mode_changed                   │                │
                              │                         │                          │                │                │
                              └─────────────────────────┴──────────────────────────┘                │                │
                                                         │                                            │                │
                                                         ▼                                            │                │
                                                 core.permissions                                     │                │
                                                         │                                            │                │
                                            ┌────────────┴────────────┐                               │                │
                                            │                         │                               │                │
                                            ▼                         ▼                               │                │
                                          ALLOW                     DENY                              │                │
                                            │                         │                               │                │
                                            │                         └──────────► error to UI        │                │
                                            ▼                                                          │                │
                                       PYTHON CORE  (python/core/)                                     │                │
                                            │                                                          │                │
    ┌───────────┬───────────┬───────────┬──┴────────┬───────────┬───────────┬───────────┬───────────┐  │                │
    │           │           │           │           │           │           │           │           │  │                │
    ▼           ▼           ▼           ▼           ▼           ▼           ▼           ▼           ▼  │                │
 database   serial_    device_     commands    attendance  attendance_ attendance_    auth       permissions           │                │
    │       handler   discovery       │            │        status     calendar        │             │               │
    │           │           │         │            │           │           │           │             │               │
    ▼           ▼           ▼         ▼            ▼           ▼           ▼           ▼             ▼               │
 students   COM mgmt   enumerate  SCAN/STOP    parse lines  time_in    holidays     PBKDF2-HMAC-   Guest/Teacher/     │
 attendance connection  ports      ENROLL      parse JSON   time_out   suspensions  SHA256          Administrator     │
 card_uid   read/write  rank       DELETE      fingerprint  early      half-days    salt gen.       role hierarchy    │
 enroll_dt  line buffer candidates  WIPE       processing   late       weekday      password        session lock/     │
 updated_dt device state probe:ID?  LIST       RFID proc.   absent     exclusions   creation        timeout           │
            auto      validate    CARD_WRITE  unknown       rules      date-specific                                 │
            reconnect  identity    _HEX       handling                 schedule                                      │
                       + protocol  CARD_ERASE  unknown                                                              │
                       version                 classif.                                                             │
                                                UID normal.                                                            │
                                                AES-GCM val.                                                          │
                                                cooldown                                                              │
                                                persistence                                                           │
    │           │           │         │            │           │           │           │             │               │
    └───────────┴───────────┴─────────┴──────┬─────┴───────────┴───────────┴───────────┴─────────────┘               │
                                             │                                                                        │
                    ┌────────────────────────┼─────────────────────────┐                                             │
                    ▼                        ▼                         ▼                                             │
               rfid_card                 logger.py              setup_wizard.py                                      │
              (core/rfid_card.py)              │                       │                                             │
                    │                console/file/UI buffer     password / device /                                  │
              AES key create/store          │                   schedule / branding                                  │
              UID normalization              │                   steps, resume state                                 │
              payload construction          │                       │                                                │
              AES-GCM encrypt/decrypt        │                       │                                                │
              auth-tag validation            │                       │                                                │
              payload-version validation     │                       │                                                │
              student identity extraction    │                       │                                                │
                    │                        │                       │                                                │
                    │                firmware_helper.py         utils.py                                              │
                    │                (discovery, build/upload)  (JSON/date/shared helpers)                            │
                    │                        │                       │                                                │
                    │                services/                                                                       │
                    │                ├── student_service.py (thin wrapper → core)                                    │
                    │                └── attendance_service.py (thin wrapper → core)                                 │
                    │                                                                                                 │
                    └──────────────────────────────────────────────────────────────────────────────────────────────── ┘
                                                         │
                                                         ▼
                                                device_discovery ◄──────────────────────────────────────────────────┐
                                                         │                                                          │
                                                         ▼                                                          │
                                                  adopt working port                                                │
                                                         │                                                          │
                                                         ▼                                                          │
                                                   SerialHandler                                                    │
                                                         │                                                          │
                                                         ▼                                                          │
                                                 USB SERIAL 115200                                                  │
                                                         │                                                          │
                                                         ▼                                                          │
                                          ESP32_DSIS_AllInOne.ino  (active firmware)                                │
                                                         │                                                          │
        ┌─────────────────────┬───────────────┴───────────────┬─────────────────────┐                              │
        │                     │                                │                     │                              │
        ▼                     ▼                                ▼                     ▼                              │
  HOST INTERFACE      FINGERPRINT ENGINE                 RFID ENGINE            LED MANAGER                          │
        │                     │                                │                     │                              │
   ID? / SCAN            getImage()                     Detect card           ledReady / ledScan                    │
   STOP / ENROLL         image2Tz()                      Read UID             ledEnroll / ledSuccess                 │
   ENROLL:<id>           fingerSearch()                   Detect family        ledError / ledSleep                   │
   DELETE:<id>           createModel()                   (Classic / Type2 /   ledFirmware                            │
   WIPE / LIST           storeModel()                     Other)              ledHostConnected /                     │
   CARD_WRITE_HEX        loadModel()                     Family-specific      ledHostDisconnected                    │
   CARD_ERASE            deleteModel()                    adapter selected                                           │
   STATUS:<state>        template count                        │                     │                              │
        │                     │                                │                     │                              │
        │                     ▼                                ▼                     │                              │
        │                   AS608                       CardDetector                 │                              │
        │                UART2 57600                        SPI BUS                  │                              │
        │                     │                                │                     │                              │
        │                     │           ┌────────────────────┼────────────────────┐│                              │
        │                     │           │                    │                    ││                              │
        │                     │           ▼                    ▼                    ▼│                              │
        │                     │       CLASSIC                TYPE 2               OTHER                             │
        │                     │  (Mini / 1K / 4K)     (Ultralight / NTAG215/216)  (MIFARE Plus, DESFire/            │
        │                     │           │                    │              ISO14443-4, ambiguous — detection-     │
        │                     │           ▼                    ▼              only or unsupported)                  │
        │                     │    ClassicAdapter        Type2Adapter                │                              │
        │                     │    ├── authenticate      ├── read pages 4–15         │                              │
        │                     │    ├── read blocks       ├── write pages             │                              │
        │                     │    ├── write blocks      └── verify readback         │                              │
        │                     │    └── verify readback         │                     │                              │
        │                     │           │                    │                     │                              │
        │                     │           └─────────┬──────────┘                     │                              │
        │                     │                     ▼                                │                              │
        │                     │            48-byte DSIS envelope                      │                              │
        │                     │                     │                                │                              │
        │                     │                     ▼                                │                              │
        │                     │           STRUCTURED JSON EVENT ◄──────────── unreadable → UNKNOWN                   │
        │                     │                     │                                                                │
        └─────────────────────┴─────────────────────┤                                                                │
                                                    ▼                                                                 │
                                          USB SERIAL 115200                                                          │
                                                    │                                                                 │
                                                    ▼                                                                 │
                                             SerialHandler                                                           │
                                                    │                                                                 │
                                                    ▼                                                                 │
                                          AttendanceProcessor                                                        │
                                                    │                                                                 │
        ┌─────────────────────────────────────────┼─────────────────────────────────────┐                          │
        │                                          │                                     │                          │
        ▼                                          ▼                                     ▼                          │
   process_line()                        lookup_student()                       all_students()                      │
   reset()                               lookup_card_student()                  _is_in_cooldown()                   │
   _handle_unknown_scan()                                                       _cooldown_reason()                  │
   _handle_unknown_card_scan()                                                  _log_and_record()                   │
   _handle_card_scan()                                                                                                │
   _handle_confidence_scan()                                                                                          │
   _handle_json_match_scan()                                                                                          │
   _parse_json_int() / _parse_int_value()                                                                             │
        │                                          │                                     │                          │
        └──────────────────────────────────────────┼─────────────────────────────────────┘                          │
                                                    ▼                                                                 │
                                          IDENTITY VALIDATION                                                        │
                                                    │                                                                 │
                              ┌──────────────────────┴──────────────────────┐                                       │
                              ▼                                             ▼                                       │
                        FINGERPRINT                                       RFID                                      │
                              │                                             │                                       │
                              ▼                                             ▼                                       │
                       fingerprint_id (1–127;                        48-byte envelope: payload version,             │
                       0 reserved = Unregistered)                     random 12-byte nonce, AES-GCM                  │
                              │                                       ciphertext + auth tag                          │
                              │                                             │                                       │
                              │                                             ▼                                       │
                              │                                   AES-GCM decrypt (UID-bound AAD)                    │
                              │                                   ├── validate auth tag                              │
                              │                                   ├── validate payload version                       │
                              │                                   └── extract fingerprint_id + student_no             │
                              │                                             │                                       │
                              │                              ┌──────────────┴──────────────┐                        │
                              │                              │                             │                        │
                              │                           INVALID                        VALID                      │
                              │                              │                             │                        │
                              │                              ▼                             ▼                        │
                              │                          UNKNOWN                  Student lookup + compare           │
                              │                                                    (DB student_no, DB card_uid)      │
                              │                                                             │                        │
                              │                                                 ┌───────────┴───────────┐            │
                              │                                                 │                       │            │
                              │                                               FAIL                     PASS          │
                              │                                                 │                       │            │
                              │                                                 ▼                       ▼            │
                              │                                              UNKNOWN             Cooldown check      │
                              │                                                                          │            │
                              │                                                          ┌───────────────┴──────────┐ │
                              │                                                          │                          │ │
                              │                                                       BLOCKED                    ALLOWED
                              │                                                          │                          │ │
                              │                                                          ▼                          ▼ │
                              │                                                   ignore duplicate           log_attendance()
                              │                                                                                      │ │
                              └──────────────────────────────────────────────────────────────────────────────────────┤
                                                                                                                     ▼
                                                                                                              attendance_status
                                                                                                                     │
                                                                                                    ┌────────────────┼────────────────┐
                                                                                                    ▼                ▼                ▼
                                                                                                 time_in         time_out    schedule compare
                                                                                                    │                │                │
                                                                                                    └────────────────┼────────────────┘
                                                                                                                     ▼
                                                                                                                  SQLite
                                                                                                                     │
        ┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┤
        │                                                                                                          │
        ▼                                                                                                          ▼
   attendance.db                                                                                             data/ tree
        │                                                                                                          │
        ├── students                                                                                     ├── attendance.db
        │    ├── fingerprint_id (PK, links to attendance.fingerprint_id)                                  ├── settings.json
        │    ├── student_no                                                                               ├── backups/
        │    ├── student_name                                                                              ├── logs/
        │    ├── grade                                                                                     ├── exports/
        │    ├── section                                                                                    ├── charts/
        │    ├── card_uid                                                                                    └── .admin_initialized
        │    ├── enrollment_date
        │    └── updated_date
        │
        └── attendance
             ├── id
             ├── fingerprint_id  (0 = Unregistered/Unknown, 1–127 = AS608 IDs)
             ├── date
             ├── time
             ├── confidence
             ├── status
             ├── timestamp
             └── event_type
        │                                                                                                          │
        └───────────────────────────────────────────────┬──────────────────────────────────────────────────────────┘
                                                        ▼
                                                 REPORTS / STATISTICS / EVALUATION
                                                        │
                                          ┌─────────────┼─────────────┐
                                          ▼             ▼             ▼
                                       REPORTS      STATISTICS    EVALUATION
                                    (daily/weekly/  (totals, by    (day/week/month;
                                     monthly)        grade/section, Excellent/Good/
                                                      timeline)     Needs attention/Low)
                                          │             │             │
                                          └─────────────┼─────────────┘
                                                        ▼
                                                  CSV export + charts
                                                        │
                                                        ▼
                                                  Api._push()
                                                        │
                                                        ▼
                                                 window.dsisEvent
                                                        │
                                                        ▼
                                                      app.js
                                                        │
                                                        ▼
                                                   UI UPDATES
                                                        │
                                                        ▼
                                                  USER RESULT
                                                        │
                                                        └──────────► next action loops back to the top
```

## Architecture summary

- User interactions begin in the desktop web app and flow through the pywebview bridge into the Python backend.
- The Python core owns permissions, device communication, attendance evaluation, data persistence, and reporting decisions.
- The ESP32 firmware acts as the hardware endpoint for the AS608 fingerprint sensor and RC522 RFID reader.
- Attendance and identity checks converge into shared validation and SQLite persistence.
- Reporting and UI updates are produced from the persisted data and fed back to the user.

This system is organized as a continuous pipeline: user input → software processing → hardware interface → data validation → persistence → reporting → user-visible results.
