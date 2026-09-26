# Architecture

These documents describe the current v3 runtime and its persistence and event contracts.

- [v3 System Architecture](v3-system.md): component boundaries and process ownership.
- [Runtime Contract](runtime-contract.md): startup, bridge calls, device synchronization, and state transitions.
- [Software Flow](software-flow.md): enrollment, scanning, attendance, and reporting flows.
- [Database Schema](database-schema.md): SQLite tables, migrations, reserved rows, and preservation rules.
- [System Architecture](system-architecture.md): broader architectural reference.
- [DSIS End-to-End Architecture Overview](dsis-end-to-end-architecture.md): full-system diagram from UI through hardware, validation, persistence, and reporting.

## Current boundary

The frontend is presentation and interaction code. `python/gui_web/api.py` is the bridge boundary. Core modules own authentication, permissions, serial parsing, attendance decisions, calendar rules, and SQLite access. Services compose those modules for student and attendance workflows. The firmware owns sensor interaction and emits the serial protocol; it does not own student names, attendance history, or application permissions.
