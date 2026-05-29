import asyncio
import ipfs_comm
import meshtastic_comm
import config
import logging
import socketio
from aiohttp import web, ClientSession
import json
import auth  # Import the authentication module
import ipfshttpclient
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

sio = socketio.AsyncServer(cors_allowed_origins='*')  # Enable CORS


def is_probable_ipfs_cid(value: str) -> bool:
    """Return True for the CID formats this gateway can safely recognize."""
    if not isinstance(value, str):
        return False

    candidate = value.strip()
    if not candidate:
        return False

    if candidate.startswith("Qm") and len(candidate) == 46:
        return True

    if candidate.startswith("b") and len(candidate) >= 10:
        return all(ch in "abcdefghijklmnopqrstuvwxyz234567" for ch in candidate)

    return False


async def process_plugin_request(ipfs_node, sio_server, session, payload: dict) -> tuple[dict, int]:
    """Handle a plugin gateway request and return a JSON response body and status."""
    request_type = payload.get('type')
    sender = payload.get('sender')

    if request_type == 'store':
        data = payload.get('data')
        if not isinstance(data, str) or not data:
            return {'error': 'data must be a non-empty string'}, 400

        cid = await ipfs_comm.add_data(ipfs_node, data.encode('utf-8'), session)
        if not cid:
            return {'error': 'failed to store data on ipfs'}, 502

        await sio_server.emit('ipfs_cid', {'original_data': data, 'cid': cid})
        return {'type': 'cid', 'cid': cid, 'sender': sender}, 200

    if request_type == 'retrieve':
        cid = payload.get('cid')
        if not is_probable_ipfs_cid(cid):
            return {'error': 'cid is invalid'}, 400

        data = await ipfs_comm.get_data(ipfs_node, cid, session)
        if data is None:
            return {'error': 'failed to retrieve data from ipfs'}, 502

        data_text = data.decode('utf-8')
        await sio_server.emit('ipfs_data', {'cid': cid, 'data': data_text})
        return {'type': 'data', 'data': data_text, 'sender': sender}, 200

    return {'error': 'type must be store or retrieve'}, 400


async def plugin_ipfs_handler(request: web.Request):
    """Handle plugin-originated IPFS store/retrieve requests over HTTP."""
    ipfs_node = request.app.get('ipfs_node')
    session = request.app.get('client_session')

    if ipfs_node is None or session is None:
        raise web.HTTPServiceUnavailable(reason='Gateway is not ready')

    try:
        payload = await request.json()
    except json.JSONDecodeError:
        raise web.HTTPBadRequest(reason='Body must be valid JSON')

    if not isinstance(payload, dict):
        raise web.HTTPBadRequest(reason='JSON body must be an object')

    response_payload, status = await process_plugin_request(ipfs_node, sio, session, payload)
    return web.json_response(response_payload, status=status)


async def main():
    """Main application function."""
    app = web.Application()
    sio.attach(app)
    app.add_routes([
        web.get('/health', health_check),
        web.post('/api/ipfs', plugin_ipfs_handler),
    ])

    # Use session
    ipfs_node = None
    meshtastic_connection = None
    async with ClientSession() as session:
        try:
            ipfs_node = await ipfs_comm.create_ipfs_node()
            if ipfs_node is None:
                logger.error("Failed to initialize IPFS. Exiting.")
                return

            app['ipfs_node'] = ipfs_node
            app['client_session'] = session

            meshtastic_connection = await meshtastic_comm.connect()
            if meshtastic_connection is None:
                logger.error("Failed to connect to Meshtastic. Exiting.")
                await ipfs_comm.stop_ipfs_node(ipfs_node)
                return

            # Add authentication middleware to the web application
            app.middlewares.append(auth.auth_middleware)

            # Register a task-creating wrapper that schedules the module-level handler
            def _meshtastic_wrapper(msg):
                # schedule handler as a task so the meshtastic thread isn't blocked
                try:
                    asyncio.create_task(handle_meshtastic_message(ipfs_node, meshtastic_connection, sio, session, msg))
                except RuntimeError:
                    # If there's no running loop, try to run the handler synchronously (best-effort)
                    asyncio.run(handle_meshtastic_message(ipfs_node, meshtastic_connection, sio, session, msg))

            meshtastic_comm.set_message_callback(_meshtastic_wrapper)

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


async def handle_meshtastic_message(ipfs_node, meshtastic_connection, sio_server, session, message):
    """Module-level handler for Meshtastic messages.

    This is extracted for easier testing and to allow scheduling from other threads.
    """
    try:
        if getattr(message, 'decoded', None) and message.decoded.get('portnum') == config.IPFS_PORT:
            payload_bytes = message.decoded.get('payload')
            if not isinstance(payload_bytes, (bytes, bytearray)):
                logger.error("Invalid payload type")
                return
            try:
                payload_str = bytes(payload_bytes).decode('utf-8')
            except UnicodeDecodeError:
                logger.error("Failed to decode payload")
                return

            sender_id = (
                getattr(message, 'from_id', None)
                or getattr(message, 'from', None)
                or getattr(message, 'fromId', None)
                or (message.get('from') if isinstance(message, dict) else None)
            )

            if is_probable_ipfs_cid(payload_str):
                cid = payload_str
                logger.info(f"Received CID: {cid} from Meshtastic")
                data = await ipfs_comm.get_data(ipfs_node, cid, session)
                if data:
                    logger.info(f"Retrieved data from IPFS: {data[:100]}...")
                    await meshtastic_comm.send_message(
                        meshtastic_connection,
                        data.decode('utf-8'),
                        destination_node=sender_id,
                        port=config.IPFS_PORT,
                    )
                    await sio_server.emit('ipfs_data', {'cid': cid, 'data': data.decode('utf-8')})
                else:
                    logger.error(f"Failed to retrieve data for CID: {cid}")
            else:
                data_bytes = payload_bytes
                data_str = payload_str
                logger.info(f"Received data from Meshtastic: {data_str[:100]}...")
                cid = await ipfs_comm.add_data(ipfs_node, data_bytes, session)
                if cid:
                    logger.info(f"Stored data on IPFS, CID: {cid}")
                    await meshtastic_comm.send_message(
                        meshtastic_connection,
                        cid,
                        destination_node=sender_id,
                        port=config.IPFS_PORT,
                    )
                    await sio_server.emit('ipfs_cid', {'original_data': data_str, 'cid': cid})
                else:
                    logger.error("Failed to store data on IPFS")
    except Exception as e:
        logger.error(f"Error handling Meshtastic message: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
