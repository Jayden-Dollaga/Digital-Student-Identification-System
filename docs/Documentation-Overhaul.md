# DSIS Documentation Overhaul

This manifest records the current documentation architecture and the repository-wide accuracy pass completed on 2026-09-20.

## Documentation goals

The documentation set is intended to answer four practical questions:

1. How do I install and operate DSIS?
2. How does the current v3 system work?
3. How do I develop, test, package, and troubleshoot it?
4. Which files are historical, generated, or research-only?

## Current documentation structure

~~~text
docs/
├── Architecture/        Runtime, data flow, database, v3 design
├── Hardware/            ESP32, AS608, wiring, firmware
├── UserGuide/           Installation, workflows, validation
├── Troubleshooting/     Current recovery procedures
├── Development/         Source maps, database, logs, runtime data, tools
├── API/                 JavaScript-to-Python bridge reference
├── History/             v1/v2/v3 evolution
├── generated/           Point-in-time generated reports
├── Dup/                 Preserved duplicate/superseded material
├── Research/            Concept/research material; outside product docs
└── _inbox/              Documentation asset intake
~~~

## Current source of truth

The maintained runtime is:

~~~text
run_web_gui.py / run_web_gui.bat
        -> python/gui_web/
        -> python/core/ + data/
        -> ESP32/AS608
~~~

Current hardware protocol:

- PC <-> ESP32: 115200 baud
- ESP32 <-> AS608: 57600 baud
- identity handshake: ID?
- minimum supported protocol: 1

Current firmware metadata:

- firmware 1.0.10
- protocol 1
- AS608
- ESP32
- sensor TX -> GPIO14
- sensor RX -> GPIO27

## Documentation accuracy corrections

The accuracy pass corrected stale statements found in older documentation:

- there is no built-in admin administrator password; first-run setup creates the password;
- attendance_evaluation is available to Administrator, Teacher, and Guest by default;
- application confidence 100 is a classification threshold, so 50-99 matches are labeled WEAK MATCH but are still recorded;
- device wipe is coordinated with local student/attendance cleanup after confirmed hardware success;
- v3 student deletion waits for device-confirmed fingerprint deletion before removing the local profile;
- the current v3 launcher is HTML/pywebview, not the archived Qt/CustomTkinter interfaces;
- calendar management supports holiday, suspension, and half-day exceptions;
- runtime data is external/local and SQLite is the live report source.

## Research boundary

docs/Research/ is intentionally retained but treated as concept/research material rather than product implementation documentation. Research can describe study context and future ideas without becoming the runtime contract.

## Historical and generated boundary

History/, Dup/, legacy UI directories, investigation reports, and old implementation notes preserve project provenance.

generated/ and metrics files are snapshots. They may become stale and must not override current source code, tests, or current v3 documentation.

## Maintained technical references

- Architecture/v3-system.md — current runtime contract
- Architecture/system-architecture.md — component architecture
- Architecture/software-flow.md — lifecycle and event flow
- Architecture/database-schema.md — SQLite contract
- Hardware/firmware-variants.md — device protocol and firmware
- Hardware/wiring.md — physical signal path
- UserGuide/project-overview.md — product and data model
- UserGuide/v3-workflows.md — operator workflows
- UserGuide/installation-guide.md — installation
- UserGuide/testing-results.md — documented validation
- Troubleshooting/README.md — recovery
- Development/FILES_DETAILED.md — active Python modules
- Development/runtime-data.md — runtime storage policy
- Development/logging-guide.md — logging
- API/README.md — bridge/API reference

## Maintenance rule

Whenever behavior changes, update the documentation closest to that behavior in the same change when practical. Include exact defaults, commands, paths, failure behavior, and a review date.

Last reviewed: 2026-09-20.
