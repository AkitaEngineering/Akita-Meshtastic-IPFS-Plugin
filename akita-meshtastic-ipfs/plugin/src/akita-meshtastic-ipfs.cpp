// plugin/src/akita-meshtastic-ipfs.cpp - Meshtastic IPFS Integration Plugin (Kennel)

#include "akita-meshtastic-ipfs.h"
#include "meshtastic.h"
#include "ArduinoJson.h"
#include "TimeLib.h"
#include "WiFi.h" // Include WiFi for network communication

namespace AkitaMeshtasticIPFS {

bool isEnabled = true;
IPAddress gatewayAddress;
uint16_t gatewayPort = 8080;
unsigned long lastProgressUpdate = 0;
const int MAX_MESSAGE_SIZE = 256;
WiFiClient wifiClient;
int wifi_retry_count = 0;
const int MAX_WIFI_RETRIES = 10;
const unsigned long WIFI_RETRY_DELAY = 5000; // 5 seconds

void setup() {
    loadConfig();
    if (!isEnabled) {
        Serial.println("AkitaMeshtasticIPFS: Plugin disabled.");
        return;
    }
    Serial.println("AkitaMeshtasticIPFS: Initializing IPFS Plugin...");
    // Initialize WiFi
    WiFi.begin();  // No SSID or Password.  Assume already connected.
    while (WiFi.status() != WL_CONNECTED && wifi_retry_count < MAX_WIFI_RETRIES) {
        delay(WIFI_RETRY_DELAY);
        Serial.print(".");
        wifi_retry_count++;
    }
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("AkitaMeshtasticIPFS: WiFi connection failed!");
        isEnabled = false; // Disable the plugin if WiFi is not connected
        return;
    }
    Serial.print("AkitaMeshtasticIPFS: Connected to WiFi. IP address: ");
    Serial.println(WiFi.localIP());
}

void loop() {
    if (!isEnabled) return;
    displayProgress();
    // Check for data from Gateway
    if (wifiClient.available()) {
        String response = wifiClient.readStringUntil('\n');
        handleGatewayResponse(response);
    }
}


void handleMeshtasticMessage(const meshtastic_Packet &packet) {
    if (!isEnabled) {
        return;
    }
    if (packet.decoded.portnum == IPFS_PORT) {
        if (packet.decoded.payload.size() == CID_LENGTH) {
            String cid = String((char*)packet.decoded.payload.data(), packet.decoded.payload.size());
            Serial.print("AkitaMeshtasticIPFS: Received CID: ");
            Serial.println(cid);
            // Forward CID to the gateway
            sendCIDToGateway(cid, packet.from); // Pass the sender
        } else {
            // Handle regular data, store on IPFS via gateway
            String message = String((char*)packet.decoded.payload.data(), packet.decoded.payload.size());
            Serial.print("AkitaMeshtasticIPFS: Received message: ");
            Serial.println(message);
            storeDataOnIPFS(message, packet.from); // Include sender
        }
    }
}

void storeDataOnIPFS(const String &message, uint32_t senderId) {
    if (!isEnabled) {
        return;
    }
    // Send the message to the gateway to be stored on IPFS and get the CID.
    // Construct a JSON object.
    DynamicJsonDocument doc(1024);
    doc["type"] = "store";
    doc["data"] = message;
    doc["sender"] = senderId; // Include Sender ID
    String jsonMessage;
    serializeJson(doc, jsonMessage);

     // Send to Gateway
    sendDataToGateway(jsonMessage);

}

void sendCIDToGateway(const String &cid, uint32_t senderId) {
     if (!isEnabled) {
        return;
    }
    // Send the CID to the gateway to retrieve the data from IPFS.
      DynamicJsonDocument doc(1024);
    doc["type"] = "retrieve";
    doc["cid"] = cid;
     doc["sender"] = senderId;
    String jsonMessage;
    serializeJson(doc, jsonMessage);

     // Send to Gateway
    sendDataToGateway(jsonMessage);
}

void sendDataToGateway(const String &data) {
    // Send data to the gateway (IP address and port).
    if (wifiClient.connect(gatewayAddress, gatewayPort)) {
        wifiClient.println(data);
        wifiClient.println(); // Send an extra empty line to indicate end of message
        Serial.println("AkitaMeshtasticIPFS: Sent data to gateway.");
    } else {
        Serial.println("AkitaMeshtasticIPFS: Failed to connect to gateway.");
    }
    wifiClient.stop();
}


void handleGatewayResponse(const String &response) {
    // Handle the response from the gateway.
    Serial.print("AkitaMeshtasticIPFS: Received response from gateway: ");
    Serial.println(response);

    DynamicJsonDocument doc(1024);
    DeserializationError error = deserializeJson(doc, response);
    if (error) {
        Serial.println("AkitaMeshtasticIPFS: Error deserializing JSON response from Gateway");
        return;
    }

    if (doc["type"] == "cid") {
        String cid = doc["cid"];
        uint32_t sender = doc["sender"] | 0;
        Serial.print("AkitaMeshtasticIPFS: Received CID from gateway: ");
        Serial.println(cid);
        //send the CID through the meshtastic network
        meshtastic_Packet packet;
        packet.decoded.payload.clear();
        packet.decoded.payload.insert(packet.decoded.payload.begin(), cid.begin(), cid.end());
        packet.decoded.portnum = IPFS_PORT;
        packet.from = sender; // Restore the sender
        Meshtastic.sendPacket(packet);

    } else if (doc["type"] == "data") {
        String data = doc["data"];
        uint32_t sender = doc["sender"] | 0;
        Serial.print("AkitaMeshtasticIPFS: Received data from gateway: ");
        Serial.println(data);
        // Display the data
        meshtastic_Packet packet;
        packet.decoded.payload.clear();
        packet.decoded.payload.insert(packet.decoded.payload.begin(), data.begin(), data.end());
        packet.decoded.portnum = IPFS_PORT;
        packet.from = sender;
        Meshtastic.sendPacket(packet);

    } else {
        Serial.println("AkitaMeshtasticIPFS: Unknown response type from gateway.");
    }

}

bool isCID(const std::vector<uint8_t>&payload) {
    if (payload.size() != CID_LENGTH) {
        return false;
    }
    for (uint8_t byte : payload) {
        if (!isxdigit(byte)) {
            return false;
        }
    }
    return true;
}

void loadConfig() {
    DynamicJsonDocument doc(1024);
    String config = Meshtastic.getPrefs().get("akita-ipfs", "{}");
    deserializeJson(doc, config);
    isEnabled = doc["enabled"] | true;
    const char* addressStr = doc["gatewayAddress"];
    if (addressStr) {
       gatewayAddress.fromString(addressStr);
    }
    gatewayPort = doc["gatewayPort"] | gatewayPort;
}

void saveConfig() {
    DynamicJsonDocument doc(1024);
    doc["enabled"] = isEnabled;
    doc["gatewayAddress"] = gatewayAddress.toString();
    doc["gatewayPort"] = gatewayPort;
    String config;
    serializeJson(doc, config);
    Meshtastic.getPrefs().set("akita-ipfs", config);
}

void displayProgress() {
    if (millis() - lastProgressUpdate > 5000) {
        lastProgressUpdate = millis();
        Serial.println("AkitaMeshtasticIPFS: Plugin active.");
    }
}



} // namespace AkitaMeshtasticIPFS

// Kennel plugin registration
static meshtastic_PluginStaticConfig staticConfig{
    .name = "akita-ipfs",
    .version = "1.0",
    .onReceive = AkitaMeshtasticIPFS::handleMeshtasticMessage,
    .onStart = AkitaMeshtasticIPFS::setup,
    .onNodeMessage = nullptr // No direct node messages.
};

static meshtastic_Plugin plugin(staticConfig);
