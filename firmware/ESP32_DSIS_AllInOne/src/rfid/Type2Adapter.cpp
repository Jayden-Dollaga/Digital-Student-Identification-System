#include "Type2Adapter.h"

#include <string.h>

static const byte TYPE2_IO_ATTEMPTS = 3;

static bool sameType2Uid(const MFRC522::Uid &left, const MFRC522::Uid &right) {
  if (left.size != right.size) return false;
  for (byte index = 0; index < left.size; index++) {
    if (left.uidByte[index] != right.uidByte[index]) return false;
  }
  return true;
}

static bool wakeSameType2Card(MFRC522 &reader, const MFRC522::Uid &expectedUid) {
  reader.PICC_HaltA();
  reader.PCD_StopCrypto1();
  byte atqa[2];
  byte atqaSize = sizeof(atqa);
  MFRC522::StatusCode status = reader.PICC_WakeupA(atqa, &atqaSize);
  return (status == MFRC522::STATUS_OK || status == MFRC522::STATUS_COLLISION) &&
      reader.PICC_ReadCardSerial() && sameType2Uid(reader.uid, expectedUid);
}

static bool readType2Group(MFRC522 &reader, byte firstPage, byte payload[16]) {
  for (byte attempt = 0; attempt < TYPE2_IO_ATTEMPTS; attempt++) {
    byte buffer[18];
    byte bufferSize = sizeof(buffer);
    if (reader.MIFARE_Read(firstPage, buffer, &bufferSize) == MFRC522::STATUS_OK) {
      memcpy(payload, buffer, 16);
      return true;
    }
  }
  return false;
}

static bool writeType2Group(
    MFRC522 &reader,
    byte firstPage,
    const byte payload[16],
    const MFRC522::Uid &expectedUid) {
  for (byte attempt = 0; attempt < TYPE2_IO_ATTEMPTS; attempt++) {
    if (attempt > 0 && !wakeSameType2Card(reader, expectedUid)) continue;

    bool writeSucceeded = true;
    for (byte pageOffset = 0; pageOffset < 4; pageOffset++) {
      byte pageData[4];
      memcpy(pageData, payload + pageOffset * 4, sizeof(pageData));
      if (reader.MIFARE_Ultralight_Write(firstPage + pageOffset, pageData, sizeof(pageData)) != MFRC522::STATUS_OK) {
        writeSucceeded = false;
        break;
      }
    }
    if (!writeSucceeded) continue;

    byte verifyBuffer[16];
    if (readType2Group(reader, firstPage, verifyBuffer) &&
        memcmp(payload, verifyBuffer, sizeof(verifyBuffer)) == 0) {
      return true;
    }
  }
  return false;
}

bool readType2Payload(MFRC522 &reader, byte payload[48]) {
  for (byte group = 0; group < 3; group++) {
    byte firstPage = 4 + group * 4;
    if (!readType2Group(reader, firstPage, payload + group * 16)) {
      return false;
    }
  }
  return true;
}

bool writeType2Payload(MFRC522 &reader, const byte payload[48]) {
  const MFRC522::Uid expectedUid = reader.uid;
  for (byte group = 0; group < 3; group++) {
    byte firstPage = 4 + group * 4;
    if (!writeType2Group(reader, firstPage, payload + group * 16, expectedUid)) {
      return false;
    }
  }
  return true;
}
