// akita-meshtastic-ipfs.cpp - Meshtastic IPFS Integration Plugin (Kennel)

#include "akita-meshtastic-ipfs.h"
#include <IPFS_Lite.h>
#include "meshtastic.h"
#include <ArduinoJson.h>
#include <TimeLib.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "meshtastic/plugin.h"

namespace AkitaMeshtasticIPFS {

IPFS_Lite ipfs;
bool isEnabled = true;
String ipfsPeerId;
String ipfsListenAddr = "/ip4/0.0.0.0/tcp/4001";
String ipfsBootstrapNodes[] = {
    "/dnsaddr/bootstrap.libp2p.io/p2p/QmNnooDu7bfjPFHpMcxvgDLjsiLmoMMB9myZu6mfgYSLd7",
    "/dnsaddr/bootstrap.libp2p.io/p2p/QmQCU2EcMqAqQeZ9tKRddreB1FAXJmxhvypW9JntyJviuR",
    "/dnsaddr/bootstrap.libp2p.io/p2p/QmcZf59b5ZKW4otvSTkkxnpjBpizUfVh2noGuiuWT2Pgjg",
    "/dnsaddr/bootstrap.libp2p.io/p2p/QmXaXu9N5G7tZUHj67Xp7rSjK22y9yK9s16yNq9v7m75zY"
};
unsigned long lastProgressUpdate = 0;
unsigned long lastIPFSLoop = 0;
const unsigned long IPFS_LOOP_INTERVAL = 10000;
size_t maxIPFSStorage = 1024 * 1024;
bool ipfsOnlyWifi = false;

void setup() {
    loadConfig();
    if (!isEnabled) {
        Serial.println("AkitaMeshtasticIPFS: Plugin disabled.");
        return;
    }
    Serial.println("AkitaMeshtasticIPFS: Initializing IPFS...");
    if (ipfs.begin(ipfsListenAddr.c_str())) {
        ipfsPeerId = ipfs.getPeerID();
        Serial.print("AkitaMeshtasticIPFS: Peer ID: ");
        Serial.println(ipfsPeerId);
        for (const String& node : ipfsBootstrapNodes) {
            ipfs.connect(node.c_str());
        }
        Serial.println("AkitaMeshtasticIPFS: IPFS initialized.");
        xTaskCreate(ipfsTask, "IPFS Task", 4096, NULL, 1, NULL);
    } else {
        Serial.println("AkitaMeshtasticIPFS: IPFS initialization failed.");
        isEnabled = false;
    }
}

void loop() {
    // Meshtastic loop handles other tasks.
}

void ipfsTask(void *pvParameters) {
    while (1) {
        if (isEnabled) {
            if (millis() - lastIPFSLoop > IPFS_LOOP_INTERVAL) {
                ipfs.loop();
                lastIPFSLoop = millis();
            }
            displayProgress();
        }
        vTaskDelay(pdMS_TO_TICKS(5000));
    }
    vTaskDelete(NULL);
}

void handleMeshtasticMessage(const meshtastic_Packet &packet) {
    if (!isEnabled) {
        return;
    }
    if (packet.decoded.portnum == IPFS_PORT && packet.decoded.payload.size() > CID_LENGTH && isCID(packet.decoded.payload)) {
        String cid = String((char*)packet.decoded.payload.data(), packet.decoded.payload.size());
        retrieveAndDisplay(cid, packet.from);
    }
}

void sendMessageWithIPFS(const String &message) {
    if (!isEnabled) {
        return;
    }
    if(esp_get_free_heap_size() < 4096){
        Serial.println("AkitaMeshtasticIPFS: Not enough free memory to send via IPFS.");
        return;
    }
    DynamicJsonDocument doc(1024);
    doc["message"] = message;
    doc["sender"] = Meshtastic.getNodeNum();
    doc["timestamp"] = now();
    String jsonString;
    serializeJson(doc, jsonString);
    String cid = ipfs.addString(jsonString.c_str());
    if (cid.length() > 0) {
        meshtastic_Packet packet;
        packet.decoded.payload.clear();
        packet.decoded.payload.insert(packet.decoded.payload.begin(), cid.begin(), cid.end());
        packet.decoded.portnum = IPFS_PORT;
        Meshtastic.sendPacket(packet);
    } else {
        Serial.println("AkitaMeshtasticIPFS: IPFS add failed.");
    }
}

void retrieveAndDisplay(const String &cid, uint32_t senderId) {
    if (!isEnabled) {
        return;
    }
    if(esp_get_free_heap_size() < 4096){
        Serial.println("AkitaMeshtasticIPFS: Not enough free memory to retrieve IPFS data.");
        return;
    }
    String data = ipfs.getString(cid.c_str());
    if (data.length() > 0) {
        DynamicJsonDocument doc(1024);
        deserializeJson(doc, data);
        Serial.print("AkitaMeshtasticIPFS: IPFS Message from ");
        Serial.print(senderId);
        Serial.print(" at ");
        Serial.print(doc["timestamp"].as<unsigned long>());
        Serial.print(": ");
        Serial.println(doc["message"].as<String>());
    } else {
        Serial.println("AkitaMeshtasticIPFS: IPFS get failed.");
    }
}

bool isCID(const std::vector<uint8_t> &payload) {
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
    ipfsListenAddr = doc["listenAddr"] | ipfsListenAddr;
    maxIPFSStorage = doc["maxStorage"] | maxIPFSStorage;
    ipfsOnlyWifi = doc["onlyWifi"] | ipfsOnlyWifi;
}

void saveConfig() {
    DynamicJsonDocument doc(1024);
    doc["enabled"] = isEnabled;
    doc["listenAddr"] = ipfsListenAddr;
    doc["maxStorage"] = maxIPFSStorage;
    doc["onlyWifi"] = ipfsOnlyWifi;
    String config;
    serializeJson(doc, config);
    Meshtastic.getPrefs().set("akita-ipfs", config);
}

void displayProgress() {
    if (millis() - lastProgressUpdate > 5000) {
        lastProgressUpdate = millis();
        Serial.print("AkitaMeshtasticIPFS: Connected Peers: ");
        Serial.print(ipfs.getConnectedPeerCount());
        Serial.print(", Free Heap: ");
        Serial.println(esp_get_free_heap_size());
    }
}

} // namespace AkitaMeshtasticIPFS

// Kennel plugin registration
static meshtastic_PluginStaticConfig staticConfig{
    .name = "akita-ipfs",
    .version = "1.0",
    .onReceive = AkitaMeshtasticIPFS::handleMeshtasticMessage,
    .onStart = AkitaMeshtasticIPFS::setup
};

static meshtastic_Plugin plugin(staticConfig);
