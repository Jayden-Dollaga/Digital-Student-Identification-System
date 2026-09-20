# DSIS Forensic Audit

**Scope:** `main` at `470d89084bc632e4ef77a71afaf5602c3a72c806`, audited on 2026-09-20.

## Executive summary

The maintained runtime is the Windows **v3 HTML/pywebview** application launched by `run_web_gui.py` / `run_web_gui.bat`, with the Python bridge in `python/gui_web/`, shared services in `python/core/`, SQLite under `data/`, and the maintained ESP32 + AS608 sketch at `firmware/ESP32_Fingerprint_AllInOne/ESP32_Fingerprint_AllInOne.ino`.

Static review did **not** identify a confirmed active critical or high-severity code vulnerability. The main confirmed findings were documentation/CI drift around the v3 migration. Safe fixes in this branch align those documents with the maintained runtime and add the documented JavaScript syntax check to CI.

## Phase 0 — repository map

### Active / maintained

- `run_web_gui.py` and `run_web_gui.bat`: supported desktop launch path.
- `python/gui_web/`: v3 HTML/pywebview UI and JavaScript-to-Python bridge.
- `python/core/`: active serial, attendance, database, authentication, permissions, discovery, logging, and utility services.
- `python/settings_store.py`, `python/config.py`: runtime configuration and local settings.
- `firmware/ESP32_Fingerprint_AllInOne/`: maintained ESP32 + AS608 firmware.
- `tests/`: current automated tests; hardware-specific tests are marked separately.
- `docs/`: current operator/developer/hardware documentation plus some explicitly historical/generated snapshots.
- `.github/workflows/tests.yml`: CI for Python compilation and automated tests.

### Historical / reference

- `archive/legacy-ui/`: v1 CustomTkinter and v2 Qt applications retained for reference.
- Historical standalone firmware under `firmware/attendance/`, `firmware/enroll/`, `firmware/delete/`, and `firmware/test/` is not the supported v3 firmware.
- `tests/legacy/`, `tests/_archives/`, `tests/Prototype/`, and similar reference material are not the maintained runtime.
- `Build/` contains PyInstaller specifications; generated build directories are ignored.
- Several files under `docs/generated/` are historical generated snapshots and can become stale if not regenerated.

## Phase 1 — findings

### Critical

**None confirmed in the active runtime by this static audit.**

### High

**None confirmed in the active runtime by this static audit.**

The current code already contains important security controls: salted PBKDF2-HMAC-SHA256 password storage, role/permission checks, parameterized SQLite queries, CSV formula-injection neutralization, and backup-restore path containment. Runtime `data/` is ignored, and direct checks for current `data/settings.json` and `driver/install/` did not find those paths tracked on `main`.

### Medium

1. **Stale generated GUI documentation described archived UI stacks as active.**
   - `docs/generated/GUI.md` listed `python/gui/` and `python/gui_qt/` as the project's two desktop interfaces and described the Qt stack as the modern interface.
   - This contradicted the maintained v3 HTML/pywebview launch path documented by `README.md`, `INSTALLATION.md`, and `PORTABLE_BUILD.md`.
   - **Fix:** rewrote the generated GUI audit snapshot to identify `python/gui_web/` as the active interface and clearly label v1/v2 material as historical/reference.

2. **Generated architecture documentation contained stale launch/deployment paths.**
   - `docs/generated/ARCHITECTURE.md` named Qt and CustomTkinter as the desktop UI layers and listed obsolete Qt launchers.
   - **Fix:** updated the architecture snapshot to describe v3 `gui_web`, `run_web_gui.py`, and the archived/reference stacks accurately.

3. **Firmware-variant documentation referenced a placeholder binary that is no longer present.**
   - `docs/Hardware/firmware-variants.md` documented `firmware/prebuilt/attendance_v1.0.bin` as a placeholder and told users not to flash it, while the referenced file is not present on `main`.
   - **Fix:** removed the nonexistent placeholder from the current variant table and replaced the section with a clear statement that no verified prebuilt binary is distributed; source firmware is the supported path.

### Low

1. **CI did not run the JavaScript syntax check documented by the installation/release guides.**
   - The workflow compiled Python and ran pytest, but did not execute `node --check python/gui_web/web/app.js`.
   - **Fix:** added the syntax-only Node check to the CI job.

2. **The ignore policy did not explicitly cover ZIP bundles produced under build/test locations.**
   - Runtime databases/logs and `driver/install/` were already correctly ignored with forward slashes.
   - **Fix:** added narrow ignore rules for build/test ZIP bundles rather than globally ignoring every ZIP file, preserving intentional repository archives.

## Protocol and data checks

- PC ↔ ESP32: **115200 baud** confirmed in the maintained firmware and active Python serial configuration.
- ESP32 ↔ AS608: **57600 baud** confirmed in the maintained firmware/documentation.
- Attendance cooldown: firmware has a 2-second scan delay; the desktop attendance processor has its own configurable cooldown (default 10 seconds). These are separate layers and were not changed.
- SQLite schema/query review found the active database layer using explicit student columns and parameterized values for user-controlled query data.
- Student/fingerprint identifiers are not intentionally written to public repository files by the active runtime. Logs can contain operational device information and should remain local as documented.

## Security review notes

- Password hashing uses PBKDF2-HMAC-SHA256 with a random 16-byte salt and 310,000 iterations.
- Active v3 API methods gate enrollment, deletion, wipe, scan, backup/restore, and export operations through permissions.
- Database restore has filesystem containment checks rather than trusting a user-selected path.
- CSV export neutralizes spreadsheet formula-trigger characters.
- No cloud API or new network dependency was introduced by this audit.
- No secrets, database files, runtime logs, or `driver/install/` content were added by this audit.

## Phase 2 — scan status

The online environment available for this audit could inspect GitHub repository contents but could not resolve `github.com` from the local command environment. A local `git clone` therefore failed before a working tree could be created.

As a result, these commands were **not executable locally** in this environment:

```text
python -m compileall python
python -m pytest -q
node --check python/gui_web/web/app.js
```

Static GitHub search/review was used instead for imports, serial constants, SQL construction, exception handling, TODO/FIXME searches, runtime paths, firmware references, and documentation drift. The repository's CI workflow remains the authoritative executable validation once the branch is pushed.

## Phase 3 — safe fixes

- Updated `docs/generated/GUI.md` for the active v3 architecture.
- Updated `docs/generated/ARCHITECTURE.md` for current launch/deployment paths.
- Updated `docs/Hardware/firmware-variants.md` to remove the nonexistent placeholder binary reference.
- Added `node --check python/gui_web/web/app.js` to `.github/workflows/tests.yml`.
- Added narrow ZIP ignore rules for build/test output to `.gitignore`.
- No baud rates, firmware protocol messages, database schema, or application workflow were rewritten.
- No archive directories were deleted.

## Phase 4 — hardware / Windows validation still required

A real Windows machine with the target hardware is still required to validate:

1. ESP32 USB driver and COM-port enumeration.
2. PC ↔ ESP32 handshake at 115200.
3. ESP32 ↔ AS608 communication at 57600.
4. Fingerprint enrollment, cancellation, deletion, and wipe.
5. Fingerprint count and scan-mode transitions.
6. Attendance cooldown and duplicate-scan behavior with real fingerprints.
7. SQLite persistence and backup/restore on a writable Windows `data/` directory.
8. CSV export in a real spreadsheet application, including formula-neutralization behavior.
9. PyInstaller v3 package launch on a clean Windows machine.
10. Reconnect behavior after physically unplugging/replugging the ESP32.

## Residual risks / follow-up

- Generated documentation snapshots should be regenerated or clearly marked historical whenever the architecture changes.
- CI cannot reproduce physical ESP32/AS608 behavior, Windows serial-driver behavior, or the packaged Windows runtime.
- The archived/reference trees intentionally contain older code and should not be treated as evidence of the active v3 implementation.

## Audit conclusion

The repository is internally consistent on the key active runtime path after these documentation/CI fixes. No confirmed active critical/high code issue was found in the static pass. The remaining meaningful validation is execution of the test suite and JavaScript syntax check in CI plus physical Windows/ESP32/AS608 testing.
