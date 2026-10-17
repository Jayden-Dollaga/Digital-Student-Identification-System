# Security Remediation Status

This document tracks the first remediation pass for the v3 DSIS desktop application. It distinguishes source changes from controls that still require deployment or physical-device validation.

## Addressed in this branch

- **Attendance eligibility:** Below-threshold fingerprint matches are diagnostic-only and are not newly written as attendance. Historical `WEAK MATCH` rows are excluded from attendance evaluation and no longer produce Time In/Out fields in exports. Dashboard/report presence counts require a qualifying status.
- **Attendance calendar:** Evaluation denominators are based on elapsed weekdays, recurring days off, and configured holidays/suspensions, not only dates when scans were recorded. Future days in the selected current period are excluded.
- **Stable identity:** Daily summaries group by fingerprint ID plus date instead of display name plus date; qualifying same-day statuses take precedence over older weak status rows.
- **Settings integrity:** Settings writes use a same-directory temporary file, flush/fsync, and atomic replacement. Invalid JSON is quarantined rather than silently overwritten; unreadable files fail visibly.
- **Database restore safety:** Restore rejects SQLite files without the required DSIS tables/columns, creates and verifies a transactionally consistent pre-restore snapshot, uses SQLite's backup API to include WAL state, and attempts rollback from the safety snapshot if the restore fails. Regression tests cover unrelated schemas, preservation of the live database, and simulated restore failure; target-Windows acceptance is still required.
- **Administrator recovery:** A malformed existing password verifier or quarantined settings file is treated as a recovery condition, not permission to rerun first-time password setup. Password verifier parameters and encoded fields are bounded, and persisted lockout deadlines are normalized.
- **RFID key handling:** Normal settings reset preserves the existing AES-GCM key. Malformed keys, quarantined settings, or a missing key while linked RFID cards exist block silent regeneration. Registration flows surface this recovery error to the UI.
- **API authorization:** Log retrieval and opening the log folder are administrator-only. Dashboard aggregates require record-read permission, student-field validation and report export are permission-checked, and internal pywebview lifecycle hooks are not exposed as public bridge methods.
- **Startup/device failure handling:** Database initialization failure aborts startup visibly. A failed AS608 initialization no longer prevents RC522 RFID operation; fingerprint-only commands are rejected when that sensor is unavailable. Match events are range-checked before recording.
- **Build/release automation:** The release workflow runs on version tags instead of every push to main. CI includes Python tests, firmware compilation, and a Windows package smoke/build check.
- **Documentation/tests:** Role, key-recovery, confidence-scale, attendance, and API-inventory documentation and regression tests have been updated.

## Remaining risks and deployment checks

These are not claimed to be solved by the source changes above:

1. **Physical serial access is still a trust boundary.** The host-connected handshake is not cryptographic device authentication. A user with direct USB/serial access and knowledge of the protocol may be able to issue firmware commands. A real fix needs an explicit device-pairing/key-provisioning design and coordinated firmware + Python protocol changes; a hardcoded public key would not provide meaningful authentication.
2. **Local files are not encrypted at rest by DSIS.** The database, settings, backups, exports, and logs remain accessible to an OS account with sufficient filesystem permissions. Use a dedicated Windows account, restrictive data-folder ACLs, full-disk encryption (such as BitLocker), and access-controlled backups. This is not a substitute for application-level encryption where the threat model requires it.
3. **RFID cloning/replay limitations remain.** AES-GCM validates payload integrity but a copied valid payload on a compatible cloned UID can still be replayed. MIFARE Classic UIDs and card contents are not a strong, clone-resistant proof of physical-card identity. Treat RFID as a convenience credential or pair it with fingerprint verification for higher assurance.
4. **Physical hardware has not been exercised by CI.** Firmware compilation cannot prove real AS608/RC522 behavior, sensor recovery, readback behavior, or timing on the actual ESP32/card types. Run supervised hardware-in-the-loop checks before using this branch with real attendance.
5. **The Windows workflow is a smoke/build check, not a full interactive acceptance test.** Launch the built application on a target Windows machine, verify WebView2 availability, login/recovery, serial connect/disconnect, backup/restore, and representative fingerprint/RFID flows.
6. **School-day policy depends on configuration.** The reporting denominator excludes weekends and applies configured recurring days off and calendar exceptions. Administrators must enter actual holidays, suspensions, and other non-class days; the application does not automatically import an official school calendar or term dates.
7. **Pre-existing data needs a careful migration test.** Before validating the branch against real records, back up the database and `data/settings.json`. In particular, do not replace/reinitialize the RFID key when existing cards are enrolled; restore the original key or intentionally re-enroll affected cards under a documented plan.
8. **Maintainability follow-up remains.** The v3 API and frontend files are large. Refactor them incrementally with contract tests rather than doing a broad rewrite in the same security patch.

## Merge gate

Do not treat this document or a successful CI badge as proof of production readiness. Before merging, confirm that the latest PR-head Python matrix, firmware build, and Windows package workflow all pass. Then complete the target-machine checks above and have a maintainer review the security-sensitive behavior changes. Keep this PR in draft until those review steps are satisfied.
