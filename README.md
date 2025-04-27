# Akita Meshtastic IPFS Plugin (Kennel Integration)

**Organization:** Akita Engineering
**Website:** [www.akitaengineering.com](www.akitaengineering.com)
**Contact Email:** info@akitaengineering.com

This Meshtastic plugin, `akita-meshtastic-ipfs`, integrates the InterPlanetary File System (IPFS) with Meshtastic, enabling decentralized data storage and retrieval over your Meshtastic network. This version is designed to be used with Meshtastic's "The Kennel" plugin framework.

## Features

* **Kennel Integration:** Seamless integration with Meshtastic's plugin framework for modularity and maintainability.
* **Decentralized Data Storage:** Store and retrieve messages and files using IPFS.
* **Offline Access:** Access previously retrieved data even without an internet connection.
* **Content Addressing:** Ensure data integrity and authenticity using IPFS CIDs.
* **Message Metadata:** Messages are stored with sender ID and timestamp.
* **Configuration:** Configure plugin settings through the Meshtastic app or CLI.
* **Resource Management:** Includes memory checks and configurable storage limits.
* **FreeRTOS Task:** IPFS operations run in a separate FreeRTOS task to prevent blocking the main Meshtastic loop.
* **Progress Indication:** Displays connected peers and free heap memory.
* **Security:** Includes basic authentication with a pre-shared key.
* **Robustness:** Implements retries and detailed error logging.

## Installation

1.  **Dependencies:**
    * Install the required libraries as described in the [Gateway Installation](#gateway-installation) and [Plugin Installation](#plugin-installation) sections.

2.  **Plugin Files:**
    * Place `akita-meshtastic-ipfs.cpp` and `akita-meshtastic-ipfs.h` in the `src/plugins` directory of your Meshtastic project.

3.  **Compile and Flash:**
    * Compile and flash the Meshtastic firmware to your devices.
    * Because the plugin is registered with The Kennel, no manual registration in `main.cpp` is required.

4.  **Configuration:**
    * Use the Meshtastic app or CLI to configure the plugin:
        * Enable or disable the plugin (`enabled`).
        * Set the IPFS gateway address (`gatewayAddress`).
        * Set the IPFS gateway port (`gatewayPort`).

## Gateway Installation

1.  **Dependencies:**
    * Install Python 3.7 or later.
    * Install the required Python packages:

        ```bash
        pip install -r gateway/requirements.txt
        ```

    * Ensure IPFS is installed and running on your system. See the [IPFS documentation](https://docs.ipfs.io/) for installation instructions.

2.  **Configuration:**
    * Configure the gateway using environment variables. See the `gateway/src/config.py` file for available options.
    * **Important:** Set a strong `PRESHARED_KEY` environment variable for authentication.
    * Example:

        ```bash
        export PRESHARED_KEY="your_secure_key"
        export MESHTASTIC_DEVICE="/dev/ttyUSB0" # Or use MESHTASTIC_HOST and MESHTASTIC_PORT
        python gateway/src/main.py
        ```

## Plugin Installation

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

## Configuration Options

###   Gateway

The following environment variables can be used to configure the gateway:

* `IPFS_PORT`: The Meshtastic port number used for IPFS communication. Default: `200`.
* `USE_MESH_INTERFACE`: Set to `True` to use a Meshtastic Mesh Interface (TCP/IP), `False` to use serial. Default: `True`.
* `MESHTASTIC_HOST`: The hostname or IP address of the Meshtastic device (for TCP/IP). Default: `127.0.0.1`.
* `MESHTASTIC_PORT`: The port number of the Meshtastic device (for TCP/IP). Default: `4444`.
* `WEB_PORT`: The port number for the SocketIO web server. Default: `8080`.
* `AUTHENTICATION_ENABLED`: Set to `True` to enable authentication, `False` to disable. Default: `True`.
* `PRESHARED_KEY`: The pre-shared key used for authentication. **Required if authentication is enabled.** Default: `secret_key` (CHANGE THIS!).

###   Plugin

The following options can be configured in the Meshtastic settings (using the app or CLI):

* `enabled`: (Boolean) Enables or disables the IPFS plugin. Default: `true`.
* `gatewayAddress`: (String) The IP address of the IPFS gateway.
* `gatewayPort`: (Integer) The port number of the IPFS gateway.

## Usage

* Once the plugin and gateway are set up, Meshtastic devices can send and receive data via IPFS.
* When sending data, the Meshtastic device sends the data to the gateway, which stores it on IPFS and returns the CID. The CID is then broadcast over the Meshtastic network.
* When receiving a CID, a Meshtastic device can request the data from the gateway, which retrieves it from IPFS and sends it back to the device.
* The gateway also provides a SocketIO interface for web applications to interact with IPFS data.

## Important Notes

* **Resource Usage:** IPFS can be resource-intensive. Monitor device memory and CPU usage, especially on the gateway.
* **Network Connectivity:** IPFS and Meshtastic require network connectivity. Ensure that your devices have a stable connection.
* **Security:** This plugin includes basic authentication. For production environments, use a more secure solution (e.g., OAuth 2.0, certificates).
* **Testing:** Thoroughly test the plugin and gateway in your specific Meshtastic environment before deployment.

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).
