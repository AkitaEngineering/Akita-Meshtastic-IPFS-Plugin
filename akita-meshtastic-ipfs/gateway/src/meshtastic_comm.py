from meshtastic import SerialInterface, MeshInterface  # Import MeshInterface
import logging
import asyncio
import sys
from typing import Optional

logger = logging.getLogger(__name__)
MESHTASTIC_RETRY_COUNT = 3
MESHTASTIC_RETRY_DELAY = 5

mesh_connection: Optional[SerialInterface] = None
message_callback = None


async def connect() -> Optional[SerialInterface]:
    """Connects to the Meshtastic network."""
    global mesh_connection
    for attempt in range(MESHTASTIC_RETRY_COUNT):
        try:
            if config.USE_MESH_INTERFACE:
                mesh_connection = MeshInterface(
                    hostname=config.MESHTASTIC_HOST, port=config.MESHTASTIC_PORT
                )
            else:
                mesh_connection = SerialInterface(port=config.MESHTASTIC_DEVICE)
            logger.info("Connected to Meshtastic")
            return mesh_connection
        except Exception as e:
            logger.error(
                f"Error connecting to Meshtastic (attempt {attempt + 1}/{MESHTASTIC_RETRY_COUNT}): {e}"
            )
            if attempt < MESHTASTIC_RETRY_COUNT - 1:
                await asyncio.sleep(MESHTASTIC_RETRY_DELAY)
            else:
                logger.error("Failed to connect to Meshtastic after multiple retries. Exiting.")
                sys.exit(1)  # Exit if Meshtastic connection fails
    return None



async def disconnect(connection: SerialInterface):
    """Disconnects from the Meshtastic network."""
    try:
        connection.close()
        logger.info("Disconnected from Meshtastic")
    except Exception as e:
        logger.error(f"Error disconnecting from Meshtastic: {e}", exc_info=True)



async def send_message(connection: SerialInterface, message: str, destination_node: Optional[int] = None, port: int = 200):
    """Sends a message over the Meshtastic network."""
    try:
        connection.send_message(message, destination_node, port)
        logger.info(f"Sent message: {message[:100]}... to {destination_node}, port {port}")  # Log first 100
    except Exception as e:
        logger.error(f"Error sending message: {e}", exc_info=True)



def set_message_callback(callback):
    """Sets the callback function for handling received messages."""
    global message_callback
    message_callback = callback



def on_meshtastic_message(packet, interface):
    """Handles incoming Meshtastic packets."""
    if message_callback:
        asyncio.run(message_callback(packet))



def get_node_id():
    """Gets the node ID."""
    if mesh_connection is not None:
        return mesh_connection.my_node_num
    return None
