# Settings and RFID-key recovery

DSIS stores its live settings in `data/settings.json` (or the corresponding `data` directory beside the executable for packaged builds). This file contains preferences, the administrator password verifier, calendar/schedule data, and the AES-GCM application key used by enrolled RFID cards. The SQLite database backups do **not** include that key.

## Before recovery

1. Close DSIS completely so no process can write the settings file.
2. Copy the entire data directory to a safe location. Include `settings.json`, any `settings.json.corrupt-*` files, `.admin_initialized`, `attendance.db`, and backups. Restrict access to this copy; it contains private attendance data and may contain encryption keys.
3. Do not delete the quarantined settings file or clear the administrator-initialization marker just to get past a startup issue.

## If a trusted settings backup exists

Restore a trusted copy of `settings.json` with the original `auth` record and `rfid_aes_gcm_key`. Keep the current database backed up separately. Start DSIS and verify the administrator login and a known enrolled test card before using it for attendance.

Restoring only `attendance.db` does not restore the RFID key. If the restored database references cards encrypted with a different key, those cards will not decrypt.

## If the settings JSON is malformed or unreadable

Malformed JSON or a non-object JSON document is moved to a timestamped `settings.json.corrupt-*` file so the original bytes are retained. DSIS uses default settings for repair, and an existing `.admin_initialized` marker still prevents silently creating a new administrator password.

If the original RFID key cannot be recovered, DSIS intentionally refuses to generate a replacement key automatically while quarantined settings remain. This prevents a key rotation from making every currently enrolled card appear tampered with. Do not point the app at live attendance records until the recovery decision is complete.

## If the original RFID key is permanently lost

Treat every previously enrolled encrypted card as unusable until it is re-enrolled. After making and verifying an offline copy of the quarantined settings and the full data directory, an administrator may deliberately move the `settings.json.corrupt-*` files **out of the active data directory** to a safe recovery folder. The next card-enrollment/write operation can then create a new key in the current settings. This is a deliberate key reset, not a recovery of old cards; all affected cards must be rewritten and verified against the active database.

Do not delete the quarantined copies until the school has decided the old key and cards are no longer needed. Keep the card-rewrite process supervised and test with a non-production card first.

## Protection at rest

The app does not encrypt `settings.json`, the SQLite database, database backups, exports, or logs as files. Use a Windows account with appropriate filesystem permissions and full-disk encryption (such as BitLocker), and protect exported files and external backups with the same care as student records.
