#include "CardDetector.h"

RfidCardDescriptor detectRfidCard(MFRC522 &reader) {
  MFRC522::PICC_Type piccType = MFRC522::PICC_GetType(reader.uid.sak);
  switch (piccType) {
    case MFRC522::PICC_TYPE_MIFARE_MINI:
      return {piccType, "MIFARE_MINI", 320, true};
    case MFRC522::PICC_TYPE_MIFARE_1K:
      return {piccType, "MIFARE_1K", 1024, true};
    case MFRC522::PICC_TYPE_MIFARE_4K:
      return {piccType, "MIFARE_4K", 4096, true};
    case MFRC522::PICC_TYPE_MIFARE_UL: {
      byte pageBuffer[18];
      byte bufferSize = sizeof(pageBuffer);
      if (reader.MIFARE_Read(3, pageBuffer, &bufferSize) != MFRC522::STATUS_OK ||
          pageBuffer[0] != 0xE1 || (pageBuffer[1] >> 4) != 1 || pageBuffer[3] != 0) {
        return {piccType, "TYPE2_UNKNOWN", 0, false};
      }

      uint16_t userBytes = static_cast<uint16_t>(pageBuffer[2]) * 8;
      switch (pageBuffer[2]) {
        case 0x06:
          return {piccType, "MIFARE_ULTRALIGHT", userBytes, userBytes >= 48};
        case 0x3E:
          return {piccType, "NTAG_215", userBytes, userBytes >= 48};
        case 0x6D:
          return {piccType, "NTAG_216", userBytes, userBytes >= 48};
        case 0x12:
          return {piccType, "TYPE2_144B_AMBIGUOUS", userBytes, false};
        default:
          return {piccType, "TYPE2_UNKNOWN", userBytes, false};
      }
    }
    case MFRC522::PICC_TYPE_MIFARE_PLUS:
      return {piccType, "MIFARE_PLUS", 0, false};
    case MFRC522::PICC_TYPE_MIFARE_DESFIRE:
      return {piccType, "MIFARE_DESFIRE", 0, false};
    case MFRC522::PICC_TYPE_ISO_14443_4:
      return {piccType, "ISO14443_4_UNCLASSIFIED", 0, false};
    default:
      return {piccType, "UNKNOWN", 0, false};
  }
}
