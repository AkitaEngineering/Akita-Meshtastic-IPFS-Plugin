import asyncio
import ipfs_comm
import meshtastic_comm
import config
import logging
import socketio
from aiohttp import web, ClientSession
import json
import auth  # Import the authentication module
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

sio = socketio.AsyncServer(cors_allowed_origins='*')  # Enable CORS


async def main():
    """Main application function."""
    app = web.Application()
    sio.attach(app)
    app.add_routes([web.get('/health', health_check)])

    # Use session
    async with ClientSession() as session:
        try:
            ipfs_node: Optional[ipfshttpclient.AsyncHTTPClient] = await ipfs_comm.create_ipfs_node()
            if ipfs_node is None:
                logger.error("Failed to initialize IPFS. Exiting.")
                return

            meshtastic_connection = await meshtastic_comm.connect()
            if meshtastic_connection is None:
                logger.error("Failed to connect to Meshtastic. Exiting.")
                await ipfs_comm.stop_ipfs_node(ipfs_node)
                return

            # Add authentication middleware to the web application
            app.middlewares.append(auth.auth_middleware)

            async def on_meshtastic_message(message):
                """Callback for handling Meshtastic messages."""
                try:
                    if message.decoded and message.decoded.get('portnum') == config.IPFS_PORT:
                        cid_or_data = message.decoded.get('payload')
                        if cid_or_data:
                            if isinstance(cid_or_data, str) and len(cid_or_data) == config.CID_LENGTH:
                                cid = cid_or_data
                                logger.info(f"Received CID: {cid} from Meshtastic")
                                data = await ipfs_comm.get_data(ipfs_node, cid, session)
                                if data:
                                    logger.info(f"Retrieved data from IPFS: {data[:100]}...")  # Log only the first 100 bytes
                                    # Send data back to Meshtastic and via SocketIO
                                    await meshtastic_comm.send_message(
                                        meshtastic_connection,
                                        data.decode('utf-8'),
                                        destination_node=message.from_id,
                                        port=config.IPFS_PORT,
                                    )
                                    await sio.emit('ipfs_data', {'cid': cid, 'data': data.decode('utf-8')})
                                else:
                                    logger.error(f"Failed to retrieve data for CID: {cid}")
                            else:  # Assume it's data to store
                                data_bytes = cid_or_data  # Rename
                                data_str = data_bytes.decode('utf-8')
                                logger.info(f"Received data from Meshtastic: {data_str[:100]}...")
                                cid = await ipfs_comm.add_data(ipfs_node, data_bytes, session)
                                if cid:
                                    logger.info(f"Stored data on IPFS, CID: {cid}")
                                    # Send CID back to Meshtastic and via SocketIO
                                    await meshtastic_comm.send_message(
                                        meshtastic_connection,
                                        cid,
                                        destination_node=message.from_id,
                                        port=config.IPFS_PORT,
                                    )
                                    await sio.emit('ipfs_cid', {'original_data': data_str, 'cid': cid})
                                else:
                                    logger.error("Failed to store data on IPFS")
                except Exception as e:
                    logger.error(f"Error handling Meshtastic message: {e}", exc_info=True)

            meshtastic_comm.set_message_callback(on_meshtastic_message)

            async def handle_client(sid, environ):
                """Handles new SocketIO client connections."""
                # The auth_middleware should handle authentication.
                logger.info(f"New client connected: {sid}")
                await sio.emit('connected', {'sid': sid}, room=sid)

            sio.on('connect', handle_client)

            # start the web server.
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, '0.0.0.0', config.WEB_PORT)  # Use the port from config
            await site.start()

            while True:
                await asyncio.sleep(1)  # Keep the main loop running
        except Exception as e:
            logger.error(f"Main loop error: {e}", exc_info=True)
        finally:
            if ipfs_node:
                await ipfs_comm.stop_ipfs_node(ipfs_node)
            if meshtastic_connection:
                await meshtastic_comm.disconnect(meshtastic_connection)


async def health_check(request):
    """Health check endpoint."""
    return web.Response(text="OK", status=200)


if __name__ == "__main__":
    asyncio.run(main())
