#pragma once

#include <MFRC522.h>
#include <stdint.h>

struct RfidCardDescriptor {
  MFRC522::PICC_Type piccType;
  const char *cardType;
  uint16_t userBytes;
  bool supported;
};

RfidCardDescriptor detectRfidCard(MFRC522 &reader);
