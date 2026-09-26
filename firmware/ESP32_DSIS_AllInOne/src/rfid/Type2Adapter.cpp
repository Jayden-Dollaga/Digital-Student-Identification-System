#include "Type2Adapter.h"

#include <string.h>

bool readType2Payload(MFRC522 &reader, byte payload[48]) {
  for (byte group = 0; group < 3; group++) {
    byte buffer[18];
    byte bufferSize = sizeof(buffer);
    byte firstPage = 4 + group * 4;
    if (reader.MIFARE_Read(firstPage, buffer, &bufferSize) != MFRC522::STATUS_OK) {
      return false;
    }
    memcpy(payload + group * 16, buffer, 16);
  }
  return true;
}

bool writeType2Payload(MFRC522 &reader, const byte payload[48]) {
  for (byte group = 0; group < 3; group++) {
    byte firstPage = 4 + group * 4;
    for (byte pageOffset = 0; pageOffset < 4; pageOffset++) {
      byte pageData[4];
      memcpy(pageData, payload + group * 16 + pageOffset * 4, sizeof(pageData));
      if (reader.MIFARE_Ultralight_Write(firstPage + pageOffset, pageData, sizeof(pageData)) != MFRC522::STATUS_OK) {
        return false;
      }
    }

    byte verifyBuffer[18];
    byte verifySize = sizeof(verifyBuffer);
    if (reader.MIFARE_Read(firstPage, verifyBuffer, &verifySize) != MFRC522::STATUS_OK ||
        memcmp(payload + group * 16, verifyBuffer, 16) != 0) {
      return false;
    }
  }
  return true;
}
