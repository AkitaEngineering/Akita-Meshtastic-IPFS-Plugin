// plugin/src/akita-meshtastic-ipfs.h

#ifndef AKITA_MESHTASTIC_IPFS_H
#define AKITA_MESHTASTIC_IPFS_H

#include <Arduino.h>
#include <vector>
#include <string>
#include "IPAddress.h"
#include "WiFi.h"

namespace AkitaMeshtasticIPFS {

const int CID_LENGTH = 46;
const int IPFS_PORT = 200;

extern bool isEnabled;
extern IPAddress gatewayAddress;
extern uint16_t gatewayPort;
extern WiFiClient wifiClient;


void setup();
void loop();
void handleMeshtasticMessage(const meshtastic_Packet &packet);
void sendMessageWithIPFS(const String &message, uint32_t senderId);
void retrieveAndDisplay(const String &cid, uint32_t senderId);
bool isCID(const std::vector<uint8_t> &payload);
void loadConfig();
void saveConfig();
void displayProgress();
void sendDataToGateway(const String &data);
void handleGatewayResponse(const String &response);


} // namespace AkitaMeshtasticIPFS

#endif // AKITA_MESHTASTIC_IPFS_H
