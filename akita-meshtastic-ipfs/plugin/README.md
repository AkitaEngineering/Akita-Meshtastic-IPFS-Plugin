#   Akita Meshtastic IPFS Plugin

This Meshtastic plugin integrates the InterPlanetary File System (IPFS) with Meshtastic, enabling decentralized data storage and retrieval. This plugin is designed to communicate with an IPFS gateway.

##   Features

* **IPFS Gateway Communication:** Communicates with a remote IPFS gateway over Wi-Fi.
* **Decentralized Data Storage:** Sends and receives data to/from IPFS via the gateway.
* **Offline Access:** Relies on the gateway and IPFS for offline access capabilities.
* **Content Addressing:** Handles IPFS CIDs for data integrity.
* **Message Metadata:** Includes sender ID and timestamp in IPFS messages.
* **Configuration:** Configurable via Meshtastic settings.
* **Resource Management:** Includes memory checks.

##   Installation

1.  **Dependencies:**
    * You'll need the Meshtastic development environment set up for your specific platform (e.g., Arduino IDE for ESP32).
    * Install the following libraries:
        * `IPFS_Lite`
        * `ArduinoJson`
        * `TimeLib`
        * `WiFi` (for ESP32)

2.  **Include Plugin Files:**
    * Place `akita-meshtastic-ipfs.cpp` and `akita-meshtastic-ipfs.h` in the `src/plugins` directory of your Meshtastic project.

3.  **Compile and Flash:**
    * Compile and flash the Meshtastic firmware to your devices.

##   Configuration

The following options can be configured in the Meshtastic settings (using the app or CLI):

* `enabled`: (Boolean) Enables or disables the IPFS plugin. Default: `true`.
* `gatewayAddress`: (String) The IP address of the IPFS gateway.
* `gatewayPort`: (Integer) The port number of the IPFS gateway.

##   Usage

* Once the plugin is installed and configured, Meshtastic devices will communicate with the IPFS gateway to send and receive data via IPFS.
* The ESP32 device needs to be connected to the same Wi-Fi network as the IPFS gateway.

##   Important Notes

* **Wi-Fi Dependency:** This plugin requires a Wi-Fi connection to communicate with the IPFS gateway.
* **Gateway Dependency:** An IPFS gateway must be set up and running for this plugin to function.
* **Resource Usage:** While this plugin is designed to be lightweight, Wi-Fi communication and JSON processing can still consume resources.
* **Testing:** Thoroughly test the plugin in your Meshtastic environment.

##   License

This project is licensed under the [GNU General Public License v3.0](LICENSE).
