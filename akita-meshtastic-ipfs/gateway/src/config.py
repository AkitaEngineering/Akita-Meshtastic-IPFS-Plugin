"""Configuration settings for the IPFS gateway."""

import os

IPFS_PORT = 200  # Port number for IPFS messages
# MESHTASTIC_DEVICE = '/dev/ttyUSB0'  # Serial port for Meshtastic. Remove hardcoded serial port
USE_MESH_INTERFACE = os.environ.get("USE_MESH_INTERFACE", "True").lower() == "true"  # Use TCP/IP
MESHTASTIC_HOST = os.environ.get("MESHTASTIC_HOST", "127.0.0.1")  # IP of device
MESHTASTIC_PORT = int(os.environ.get("MESHTASTIC_PORT", "4444"))  # Port
WEB_PORT = int(os.environ.get("WEB_PORT", "8080"))  # Port for the web server
CID_LENGTH = 46
AUTHENTICATION_ENABLED = os.environ.get("AUTHENTICATION_ENABLED", "True").lower() == "true"
PRESHARED_KEY = os.environ.get("PRESHARED_KEY", "secret_key")  # Change this!
