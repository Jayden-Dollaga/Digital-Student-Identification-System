#pragma once

#include <MFRC522.h>

bool readType2Payload(MFRC522 &reader, byte payload[48]);
bool writeType2Payload(MFRC522 &reader, const byte payload[48]);
