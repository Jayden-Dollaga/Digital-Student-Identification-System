# DSIS RFID Architecture — Verified Encrypted Multi-Family Design

**Status:** Architecture branch / implementation specification  
**Branch:** `architecture/rfid-verified-encrypted`  
**Scope:** Verified encrypted RFID payloads, transactional registration, card-family adapters, and advanced-family boundaries.

> This document records the intended RFID architecture for a future implementation. It does not claim that `main` already implements every capability described here.

## 1. Architectural goal

DSIS treats RFID as an identification provider rather than one hard-coded card format.

Core responsibilities are separated into:

1. PICC detection and capability discovery.
2. Family-specific read, write, erase, and verification.
3. Authenticated DSIS payload handling with AES-256-GCM.
4. Transactional SQLite updates after verified physical-card operations.
5. Attendance identity validation using the physical UID, authenticated payload, and database record.

Core invariant:

> A student/card link is not durable until the physical card contains a valid DSIS payload and DSIS has read it back and authenticated it successfully.

## 2. Runtime boundary

```text
Student / Staff
      |
DSIS v3 HTML + pywebview
      |
Python API boundary
      |
serial_handler + existing device lock
      | USB serial 115200
ESP32
  |                       |
AS608                   RC522
fingerprint             PICC reader
                            |
                    family-neutral detection
                            |
        +-------------------+-------------------+
        |                   |                   |
     Classic          Ultralight/NTAG       Advanced
     adapter              adapter         family adapters
```

The firmware owns physical sensor I/O and serial protocol behavior. Python owns student metadata, attendance policy, persistence, authorization, and application cryptography.

## 3. AES-GCM payload contract

### 3.1 Key

- 256-bit random AES key.
- Generated once for the DSIS installation.
- Persisted separately from legacy XOR material in the ignored `data/settings.json` location.
- Never embedded in firmware source.
- Never written to the RFID card.
- Distinct from the Template Archive key and any future card-family authentication keys.

Existing XOR-encoded cards require re-registration. The new implementation must not silently accept XOR as an equivalent authenticated format.

### 3.2 UID binding

The normalized card UID is used as AES-GCM additional authenticated data (AAD).

```text
AES-GCM
  key   = DSIS 256-bit application key
  nonce = fresh random nonce
  AAD   = normalized physical card UID
  data  = compact DSIS identity payload
```

This binds the encrypted identity to the physical card UID. Moving the ciphertext to another UID must fail authentication.

### 3.3 Exact 48-byte logical envelope

For the Classic implementation, the physical DSIS payload is exactly 48 bytes so it fits three 16-byte data blocks.

```text
48 bytes
+---------+--------------+-------------------+-------------+
| version | nonce 12 B   | ciphertext 19 B   | tag 16 B    |
+---------+--------------+-------------------+-------------+
 1 byte      12 bytes         19 bytes           16 bytes
```

Because AES-GCM preserves plaintext length, the compact plaintext inside the 19-byte ciphertext should use a fixed binary structure rather than JSON:

```text
19-byte plaintext
+----------------+----------+---------------------------+
| fingerprint ID | length   | student_no UTF-8 <= 17 B |
| 1 byte         | 1 byte   |                           |
+----------------+----------+---------------------------+
```

The student number must be rejected when its UTF-8 representation exceeds 17 bytes. It must never be silently truncated.

Envelope parsing must fail closed for an unknown version, malformed lengths, invalid bytes, tag failure, wrong key, or invalid identity fields.

## 4. Family-neutral detection

Detection occurs before any family-specific mutation.

```text
PICC detected
   -> UID
   -> SAK / library classification
   -> model or capability probe when required
   -> card descriptor
   -> adapter dispatch
```

The descriptor should expose at least:

- `card_type`
- normalized UID
- read capability
- write capability
- erase capability
- authentication requirement
- usable payload capacity where reliably known.

Unsupported families report type and UID with a capability-specific reason. They must not enter a write path merely because the reader detected a card.

Existing outer JSON event envelopes remain compatible; `card_type` is optional for older events.

## 5. Adapter boundary

Each family adapter owns its protocol-specific behavior:

```text
detect/capability
read_payload
write_payload
erase_payload
verify_payload
```

Generic RFID code must not contain MIFARE Classic sector assumptions.

Operation results must distinguish at least:

`SUCCESS`, `UNSUPPORTED`, `CAPACITY_INSUFFICIENT`, `AUTH_FAILED`, `LOCKED`, `READ_FAILED`, `WRITE_FAILED`, `VERIFY_FAILED`, `WRONG_CARD`, and `DEVICE_UNAVAILABLE`.

## 6. MIFARE Classic adapter

Initial certified family targets:

- MIFARE Classic Mini
- MIFARE Classic 1K
- MIFARE Classic 4K

The existing Classic key-candidate dictionary belongs inside this adapter. It must not leak into the generic RFID dispatcher.

For the current Classic 1K target:

```text
sector 1
  block 4 -> payload 0..15
  block 5 -> payload 16..31
  block 6 -> payload 32..47
  block 7 -> sector trailer — NEVER WRITE
```

Mini and 4K must use capacity-aware valid data-sector placement rather than blindly inheriting the 1K layout.

Never write manufacturer blocks, trailers, access bits, or sector keys.

### Classic write transaction

```text
authenticate
   -> write all payload blocks
   -> read all payload blocks
   -> compare all 48 bytes
   -> authenticate/decode logical payload
   -> report verified success
```

A partial write, missing block, or readback difference is a failure.

## 7. Ultralight / NTAG adapter

Ultralight and NTAG use page-oriented memory rather than Classic sectors.

The adapter must use only commands supported by the installed and verified MFRC522 stack.

The same 48-byte logical envelope may be mapped to twelve consecutive 4-byte user pages only when the tested model has sufficient unlocked user capacity beginning at the selected user page.

Do not infer capacity from the broad family name alone.

Preserve manufacturer, capability container, lock, password/authentication, and configuration pages.

Verify every page write by reading the affected pages back before reporting success.

Initially certify only named models that have passed physical tests.

## 8. Ultralight C

Ultralight C is a separate adapter, not plain-Ultralight fallback.

The adapter must:

- identify the actual model/capacity where reliable;
- keep the page-based payload layout;
- use the documented 3DES authentication flow for protected cards;
- support only known and tested authentication states and key provisioning.

It must never modify lock/configuration pages as a shortcut, clear protection merely to gain write access, or hand-roll unverified challenge-response without test vectors.

If the installed MFRC522 stack lacks reliable Ultralight C authentication support, the card is detection/read-only/unsupported according to the verified capability rather than falsely advertised as writable.

## 9. MIFARE Plus

MIFARE Plus must never silently fall back to Classic.

Initial writable support is limited to a verified SL3 AES-authenticated path with secure messaging.

```text
detect Plus
   -> security/capability probe
       -> SL0 / SL1 / SL2 / unknown = diagnostic only
       -> verified SL3 = AES auth + secure messaging
```

DSIS-controlled AES keys may be diversified per card from a protected master using the UID as diversification input and an authenticated construction such as AES-CMAC.

Any migration of lower security levels is a separate administrative feature. It requires known current keys, verified transitions, explicit failure handling, and disposable test cards.

Never silently downgrade to Crypto1 and never treat default or unknown keys as DSIS security.

## 10. DESFire EV1

DESFire EV1 requires a separate protocol stack and adapter.

Required capabilities include ISO-DEP activation, APDU handling/chaining, DESFire application selection, authentication, secure messaging, and data-file operations.

The common MFRC522 Arduino library alone must not be assumed to provide a complete DESFire stack.

If the RC522 stack cannot reliably provide the required ISO-DEP/DESFire operations, DESFire remains detection-only on that reader and a compatible reader such as a PN532-class device plus a verified DESFire implementation is required for read/write.

The intended DSIS data model is:

```text
DESFire card
  -> DSIS AID
  -> dedicated fixed-size data file
  -> 48-byte logical DSIS envelope
```

Normal attendance must not use the factory master key or silently format an existing card.

## 11. Transactional registration

Registration follows staged physical verification before database mutation.

```text
select student
   -> detect card + capture UID
   -> reject UID already claimed by another student
   -> stage student + UID
   -> family adapter writes AES-GCM envelope
   -> read back complete payload
   -> verify GCM with UID as AAD
   -> verify fingerprint_id + student_no
   -> COMMIT SQLite card link
```

UID-only detection is never a successful registration.

Replacement failures must preserve the previous valid link. Clear pending state on cancel, timeout, stop, disconnect, or failed write.

UI stages should communicate:

`Card detected -> Writing -> Reading back -> Verifying -> Saved`.

## 12. Transactional erase

Erase is also physical-first and verified:

```text
request erase
   -> adapter clears only DSIS payload region
   -> read payload region
   -> verify expected erased state
   -> emit erase_verified
   -> unlink SQLite UID
```

Failed, partial, wrong-card, or unverified erase preserves the SQLite link.

Never erase manufacturer, trailer, lock, authentication, or unrelated configuration regions.

## 13. Attendance authentication

RFID attendance must never trust the UID alone.

```text
physical UID
    +
authenticated payload
    +
linked student UID
    +
payload fingerprint_id
    +
payload student_no
    +
SQLite student record
    -> ACCEPT
```

Any disagreement becomes an RFID-specific failure/unknown outcome.

Suggested reasons include:

- `RFID_UNKNOWN_UNLINKED`
- `RFID_UNREADABLE`
- `RFID_AUTH_FAILED`
- `RFID_PAYLOAD_INVALID`
- `RFID_IDENTITY_MISMATCH`
- `RFID_UNSUPPORTED`

The UI should distinguish these from unknown fingerprints and include the UID plus a safe reason where available.

## 14. Permissions and serial locking

Persistent RFID changes use the existing permission model. UI hiding is not authorization.

Sensitive operations include registration, replacement, unlinking, erase, batch erase, and any future personalization or migration.

The existing `serial_handler` mutex is the device serialization boundary. RFID operations, fingerprint operations, scanning transitions, periodic archive work, and other hardware actions must not create competing locks.

Long-running physical operations must hold the existing lock for the complete transaction so a live scan cannot race a multi-step RFID operation.

## 15. Relationship to the Template Archive

The RFID subsystem and the Identification Template Archive solve different problems.

| Subsystem | Purpose |
| --- | --- |
| RFID card subsystem | Stores and authenticates a student identity payload on physical cards |
| Identification Template Archive | Independently archives AS608 templates and detects template drift |

They must not share cryptographic keys or assume one can replace the other.

```text
DSIS identification
       |
       +-- RFID cards -> AES-GCM payload + UID binding
       |
       +-- AS608 -> encrypted template archive + SHA-256 drift detection
```

## 16. Compatibility and migration

Legacy XOR cards should be reported as legacy and require re-registration.

```text
legacy card
   -> detect legacy format
   -> report re-registration required
   -> new AES-GCM registration
   -> verified readback
   -> database commit
```

No fallback path should silently make the old format equivalent to the authenticated format.

## 17. Verification gates

### Python

Test AES-GCM round trips, UID AAD binding, tampering, wrong keys, malformed payloads, oversize student numbers, key persistence, legacy-card rejection, duplicate UID handling, transactional rollback, and authenticated attendance resolution.

### Firmware

Compile against the project toolchain and installed MFRC522 version. Verify real enum/function names, buffer bounds, page/block boundaries, no protected-region writes, complete readback, and disconnect/error handling.

### Hardware

Do not mark a family supported based only on library constants.

| Family | Detect | Read | Write | Readback | Erase |
| --- | --- | --- | --- | --- | --- |
| Classic Mini | required | test | test | required | test |
| Classic 1K | required | required | required | required | required |
| Classic 4K | required | test | test | required | test |
| Ultralight | required | test | test | required | test |
| Named NTAG models | required | test | test | required | test |
| Ultralight C | required | separate test | separate test | required | separate test |
| MIFARE Plus | required | SL3 test | SL3 test | required | test |
| DESFire EV1 | required | separate test | separate test | required | test |

A family becomes advertised as supported only after the required physical tests pass.

## 18. Architectural invariants

1. Never trust UID alone.
2. Never commit a card link before successful physical readback and cryptographic verification.
3. Never silently route a non-Classic card through Classic operations.
4. Never overwrite manufacturer, trailer, lock, or configuration regions as a shortcut.
5. Never treat write success as verification success.
6. Never silently accept legacy XOR cards as AES-GCM cards.
7. Never let one device operation race another device operation.
8. Never claim hardware capability beyond the tested reader/library/card combination.
9. Never let a failed physical operation cause a false successful SQLite mutation.
10. Never put application secrets or cryptographic keys in firmware source.

## 19. Implementation order

1. Freeze and test the AES-GCM 48-byte envelope.
2. Implement Classic 1K verified write/readback/erase.
3. Make registration transactional.
4. Harden attendance identity validation.
5. Add UI status/progress and failure reporting.
6. Generalize firmware detection and adapter dispatch.
7. Add Classic Mini/4K.
8. Add named tested Ultralight/NTAG models.
9. Add Ultralight C only after verified 3DES support.
10. Add MIFARE Plus SL3 only after verified secure messaging.
11. Add DESFire EV1 only with a verified ISO-DEP/DESFire stack or compatible reader.
12. Expand the physical test matrix before advertising new families.

The preferred outcome is a smaller support matrix that is verified in hardware rather than a broad matrix based only on library detection.