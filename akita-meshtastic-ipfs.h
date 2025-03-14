// akita-meshtastic-ipfs.h

#ifndef AKITA_MESHTASTIC_IPFS_H
#define AKITA_MESHTASTIC_IPFS_H

#include <Arduino.h>
#include <vector>
#include <string>
#include "esp_heap_caps.h"
#include "freertos/FreeRTOS.h"
#include "meshtastic.h"

namespace AkitaMeshtasticIPFS {

const int CID_LENGTH = 46;
const int IPFS_PORT = 200;

void setup();
void loop();
void ipfsTask(void *pvParameters);
void handleMeshtasticMessage(const meshtastic_Packet &packet);
void sendMessageWithIPFS(const String &message);
void retrieveAndDisplay(const String &cid, uint32_t senderId);
bool isCID(const std::vector<uint8_t> &payload);
void loadConfig();
void saveConfig();
void displayProgress();

} // namespace AkitaMeshtasticIPFS

#endif // AKITA_MESHTASTIC_IPFS_H
