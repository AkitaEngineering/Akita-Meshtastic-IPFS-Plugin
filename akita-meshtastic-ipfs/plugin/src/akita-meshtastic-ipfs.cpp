// plugin/src/akita-meshtastic-ipfs.cpp - Meshtastic IPFS Integration Plugin

#include "akita-meshtastic-ipfs.h"
#include "meshtastic.h"
#include "ArduinoJson.h"
#include "TimeLib.h"
#include "WiFi.h" // Include WiFi for network communication

namespace AkitaMeshtasticIPFS {

bool isEnabled = true;
IPAddress gatewayAddress;
uint16_t gatewayPort = 8080;
String gatewayKey = "secret_key";
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
}


void handleMeshtasticMessage(const meshtastic_Packet &packet) {
    if (!isEnabled) {
        return;
    }
    if (packet.decoded.portnum == IPFS_PORT) {
        if (isCID(packet.decoded.payload)) {
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
    // Send data to the gateway (IP address and port) and handle the HTTP response inline.
    if (wifiClient.connect(gatewayAddress, gatewayPort)) {
        wifiClient.setTimeout(HTTP_RESPONSE_TIMEOUT);
        wifiClient.print("POST /api/ipfs HTTP/1.1\r\n");
        wifiClient.print("Host: ");
        wifiClient.print(gatewayAddress.toString());
        wifiClient.print(":");
        wifiClient.print(gatewayPort);
        wifiClient.print("\r\n");
        wifiClient.print("Content-Type: application/json\r\n");
        wifiClient.print("Content-Length: ");
        wifiClient.print(data.length());
        wifiClient.print("\r\n");
        wifiClient.print("Connection: close\r\n");
        if (gatewayKey.length() > 0) {
            wifiClient.print("Authorization: PSK ");
            wifiClient.print(gatewayKey);
            wifiClient.print("\r\n");
        }
        wifiClient.print("\r\n");
        wifiClient.print(data);
        Serial.println("AkitaMeshtasticIPFS: Sent data to gateway.");

        String statusLine;
        String responseBody;
        if (readGatewayResponse(statusLine, responseBody)) {
            if (!statusLine.startsWith("HTTP/1.1 200") && !statusLine.startsWith("HTTP/1.0 200")) {
                Serial.print("AkitaMeshtasticIPFS: Gateway request failed: ");
                Serial.println(statusLine);
                if (responseBody.length() > 0) {
                    Serial.println(responseBody);
                }
            } else if (responseBody.length() > 0) {
                handleGatewayResponse(responseBody);
            } else {
                Serial.println("AkitaMeshtasticIPFS: Gateway response was empty.");
            }
        } else {
            Serial.println("AkitaMeshtasticIPFS: Timed out waiting for gateway response.");
        }
    } else {
        Serial.println("AkitaMeshtasticIPFS: Failed to connect to gateway.");
    }
    wifiClient.stop();
}


bool readGatewayResponse(String &statusLine, String &responseBody) {
    unsigned long startedAt = millis();
    while (!wifiClient.available() && wifiClient.connected()) {
        if (millis() - startedAt > HTTP_RESPONSE_TIMEOUT) {
            return false;
        }
        delay(10);
    }

    if (!wifiClient.available()) {
        return false;
    }

    statusLine = wifiClient.readStringUntil('\n');
    statusLine.trim();

    while (wifiClient.connected()) {
        String headerLine = wifiClient.readStringUntil('\n');
        headerLine.trim();
        if (headerLine.length() == 0) {
            break;
        }
    }

    responseBody = wifiClient.readString();
    responseBody.trim();
    return true;
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
    if (payload.empty()) {
        return false;
    }

    String candidate((const char*)payload.data(), payload.size());
    candidate.trim();

    if (candidate.startsWith("Qm") && candidate.length() == CID_LENGTH) {
        const char* base58Alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
        for (size_t i = 0; i < candidate.length(); ++i) {
            if (strchr(base58Alphabet, candidate[i]) == nullptr) {
                return false;
            }
        }
        return true;
    }

    if (candidate.startsWith("b") && candidate.length() >= 10) {
        for (size_t i = 0; i < candidate.length(); ++i) {
            char ch = candidate[i];
            if (!((ch >= 'a' && ch <= 'z') || (ch >= '2' && ch <= '7'))) {
                return false;
            }
        }
        return true;
    }

    return false;
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
    const char* keyStr = doc["gatewayKey"];
    if (keyStr && strlen(keyStr) > 0) {
        gatewayKey = keyStr;
    }
}

void saveConfig() {
    DynamicJsonDocument doc(1024);
    doc["enabled"] = isEnabled;
    doc["gatewayAddress"] = gatewayAddress.toString();
    doc["gatewayPort"] = gatewayPort;
    doc["gatewayKey"] = gatewayKey;
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

// Plugin registration
static meshtastic_PluginStaticConfig staticConfig{
    .name = "akita-ipfs",
    .version = "1.0",
    .onReceive = AkitaMeshtasticIPFS::handleMeshtasticMessage,
    .onStart = AkitaMeshtasticIPFS::setup,
    .onNodeMessage = nullptr // No direct node messages.
};

static meshtastic_Plugin plugin(staticConfig);
