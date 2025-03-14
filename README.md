# Akita-Meshtastic-IPFS-Plugin

This Meshtastic plugin, `akita-meshtastic-ipfs`, integrates the InterPlanetary File System (IPFS) with Meshtastic, enabling decentralized data storage and retrieval over your Meshtastic network. This version is designed to be used with Akita's "The Kennel" plugin framework.

## Features

* **Kennel Integration:** Seamless integration with Akitas's plugin framework for modularity and maintainability.
* **Decentralized Data Storage:** Store and retrieve messages and files using IPFS.
* **Offline Access:** Access previously retrieved data even without an internet connection.
* **Content Addressing:** Ensure data integrity and authenticity using IPFS CIDs.
* **Message Metadata:** Messages are stored with sender ID and timestamp.
* **Configuration:** Configure plugin settings through the Meshtastic app or CLI.
* **Resource Management:** Includes memory checks and configurable storage limits.
* **FreeRTOS Task:** IPFS operations run in a separate FreeRTOS task to prevent blocking the main Meshtastic loop.
* **Progress Indication:** Displays connected peers and free heap memory.

## Installation

1.  **Install Libraries:**
    * Install `IPFS_Lite` library via the Arduino Library Manager.
    * Install `ArduinoJson` library via the Arduino Library Manager.
    * Install `TimeLib` library.
2.  **Plugin Files:**
    * Place `akita-meshtastic-ipfs.cpp` and `akita-meshtastic-ipfs.h` in the `src/plugins` directory of your Meshtastic project.
3.  **Compile and Flash:**
    * Compile and flash the Meshtastic firmware to your devices.
    * Because the plugin is registered with The Kennel, no manual registration in `main.cpp` is required.
4.  **Configuration:**
    * Use the Meshtastic app or CLI to configure the plugin:
        * Enable or disable the plugin (`enabled`).
        * Set the IPFS listen address (`listenAddr`).
        * Set the maximum IPFS storage (`maxStorage`).
        * Enable IPFS operations only on Wi-Fi (`onlyWifi`).

## Configuration Options

* **`enabled`:** (Boolean) Enables or disables the IPFS plugin. Default: `true`.
* **`listenAddr`:** (String) The IPFS listen address. Default: `/ip4/0.0.0.0/tcp/4001`.
* **`maxStorage`:** (Integer) Maximum IPFS storage in bytes. Default: `1048576` (1MB).
* **`onlyWifi`:** (Boolean) Enable IPFS functions only when connected to a Wifi network. Default: `false`.

## Usage

* Once the plugin is installed and configured, Meshtastic messages can be sent and received via IPFS.
* When sending a message, the plugin will store the message on IPFS and broadcast the CID over the Meshtastic network.
* When receiving a CID, the plugin will retrieve the message from IPFS and display it.
* The `IPFS_PORT` constant defined in the `.h` file is used for all IPFS related Meshtastic messages.

## Important Notes

* **Resource Usage:** IPFS can be resource-intensive. Monitor device memory and CPU usage.
* **Network Connectivity:** IPFS relies on network connectivity.
* **Testing:** Thoroughly test the plugin in your Meshtastic environment.
* **Security:** For sensitive data, consider adding encryption and signature verification.
* **Kennel Version:** Ensure that your Akita firmware version supports The Kennel plugin framework.

## Contributing

Contributions are welcome! Please submit pull requests or open issues for bug reports or feature requests.

