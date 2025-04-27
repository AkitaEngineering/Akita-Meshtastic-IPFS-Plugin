#   IPFS Gateway for Meshtastic

This component runs on a Linux machine (e.g., Raspberry Pi) and acts as a gateway between the Meshtastic network and the IPFS network.

##   Features

* **IPFS Node:** Runs a local IPFS node.
* **Meshtastic Communication:** Connects to the Meshtastic network via serial or TCP/IP.
* **Data Bridging:** Relays data between Meshtastic and IPFS.
* **Web Interface:** Provides a SocketIO interface for web applications to interact with IPFS data.
* **Configuration:** Configurable via environment variables.
* **Authentication:** Includes basic authentication with a pre-shared key.
* **Error Handling:** Robust error handling and logging.
* **Asynchronous:** Uses `asyncio` for non-blocking operations.

##   Installation

1.  **Dependencies:**
    * Install Python 3.7 or later.
    * Install the required Python packages:

        ```bash
        pip install -r requirements.txt
        ```

    * Ensure IPFS is installed and running on your system. See the [IPFS documentation](https://docs.ipfs.io/) for installation instructions.

2.  **Configuration:**
    * Configure the gateway using environment variables. See the `config.py` file for available options.
    * **Important:** Set a strong `PRESHARED_KEY` environment variable for authentication.
    * Example:

        ```bash
        export PRESHARED_KEY="your_secure_key"
        export MESHTASTIC_DEVICE="/dev/ttyUSB0"  # Or use MESHTASTIC_HOST and MESHTASTIC_PORT
        python gateway/src/main.py
        ```

##   Running the Gateway

1.  Start the IPFS daemon:

    ```bash
    ipfs daemon
    ```

2.  Run the gateway application:

    ```bash
    python gateway/src/main.py
    ```

    The gateway will connect to Meshtastic and IPFS, and start a SocketIO server.

##   Configuration

The following environment variables can be used to configure the gateway:

* `IPFS_PORT`: The Meshtastic port number used for IPFS communication. Default: `200`.
* `USE_MESH_INTERFACE`: Set to `True` to use a Meshtastic Mesh Interface (TCP/IP), `False` to use serial. Default: `True`.
* `MESHTASTIC_HOST`: The hostname or IP address of the Meshtastic device (for TCP/IP). Default: `127.0.0.1`.
* `MESHTASTIC_PORT`: The port number of the Meshtastic device (for TCP/IP). Default: `4444`.
* `WEB_PORT`: The port number for the SocketIO web server. Default: `8080`.
* `AUTHENTICATION_ENABLED`: Set to `True` to enable authentication, `False` to disable. Default: `True`.
* `PRESHARED_KEY`: The pre-shared key used for authentication. **Required if authentication is enabled.** Default: `secret_key` (CHANGE THIS!).

##   SocketIO Interface

The gateway provides a SocketIO interface for real-time communication with web applications.

* **Events:**
    * `connect`: Emitted when a client connects.
    * `ipfs_cid`: Emitted when the gateway receives a CID from Meshtastic.
    * `ipfs_data`: Emitted when the gateway retrieves data from IPFS.

##   Authentication

The gateway uses a simple pre-shared key authentication mechanism. Clients must include an `Authorization` header with the value `PSK <pre-shared-key>`. The key is hashed using SHA256.

**Important:** This is a basic authentication method. For production environments, use a more secure solution (e.g., OAuth 2.0, certificates).
