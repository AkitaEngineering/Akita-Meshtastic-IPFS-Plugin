from meshtastic import SerialInterface, MeshInterface  # Import MeshInterface
import logging
import asyncio
import config
from typing import Optional

logger = logging.getLogger(__name__)
MESHTASTIC_RETRY_COUNT = 3
MESHTASTIC_RETRY_DELAY = 5

mesh_connection: Optional[SerialInterface] = None
message_callback = None
# Event loop where gateway's asyncio runs (set when callback is registered)
_event_loop: Optional[asyncio.AbstractEventLoop] = None


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
                logger.error("Failed to connect to Meshtastic after multiple retries.")
                return None
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
    """Sets the callback function for handling received messages and captures the running event loop.

    The Meshtastic library may invoke `on_meshtastic_message` from another thread, so we capture
    the gateway's asyncio event loop here and use thread-safe scheduling when a packet arrives.
    """
    global message_callback, _event_loop
    message_callback = callback
    try:
        _event_loop = asyncio.get_running_loop()
    except RuntimeError:
        # If called outside a running loop, leave _event_loop as None; on_meshtastic_message will fall back.
        _event_loop = None



def on_meshtastic_message(packet, interface):
    """Handles incoming Meshtastic packets from the Meshtastic library (may be called from another thread).

    If the registered `message_callback` is a coroutine function we schedule it on the captured
    asyncio event loop using `run_coroutine_threadsafe`. If it's a regular function we use
    `call_soon_threadsafe` so we don't block the Meshtastic thread.
    """
    if not message_callback:
        return

    try:
        # If we captured the gateway event loop, schedule thread-safe; otherwise try best-effort.
        if asyncio.iscoroutinefunction(message_callback):
            coro = message_callback(packet)
            if _event_loop and _event_loop.is_running():
                asyncio.run_coroutine_threadsafe(coro, _event_loop)
            else:
                # No running loop captured — run in a new loop to avoid blocking caller thread.
                asyncio.run(coro)
        else:
            if _event_loop and _event_loop.is_running():
                _event_loop.call_soon_threadsafe(message_callback, packet)
            else:
                # Best-effort synchronous call (may block caller thread)
                message_callback(packet)
    except Exception as e:
        logger.error(f"Error dispatching Meshtastic message to callback: {e}", exc_info=True)



def get_node_id():
    """Gets the node ID."""
    if mesh_connection is not None:
        return mesh_connection.my_node_num
    return None
