#pragma once

#include <MFRC522.h>

byte classicKeyCandidateCount();
const byte *classicKeyCandidate(byte index);
bool authenticateClassicCard(MFRC522 &reader, MFRC522::MIFARE_Key &activeKey, byte block, int *matchedIndex = nullptr);
bool readClassicPayload(MFRC522 &reader, byte firstBlock, byte payload[48]);
bool writeClassicPayload(MFRC522 &reader, byte firstBlock, const byte payload[48]);
