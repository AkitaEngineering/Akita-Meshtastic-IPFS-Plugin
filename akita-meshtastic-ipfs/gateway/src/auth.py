import logging
from aiohttp import web
import hashlib
import config
from typing import Optional

logger = logging.getLogger(__name__)

async def authenticate(request: web.Request) -> Optional[str]:
    """Authenticates the request using a pre-shared key."""
    if not config.AUTHENTICATION_ENABLED:
        return None  # Authentication is disabled

    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None  # No authentication header provided

    if not auth_header.startswith("PSK "):
        return None  # Invalid authentication scheme

    try:
        received_key = auth_header[4:].strip()  # Remove "PSK " prefix
        expected_key_hash = hashlib.sha256(config.PRESHARED_KEY.encode()).hexdigest()
        received_key_hash = hashlib.sha256(received_key.encode()).hexdigest()

        if received_key_hash != expected_key_hash:
            logger.warning("Authentication failed: Invalid key")
            return None  # Authentication failed
        else:
            return request.remote  # Authentication successful, return remote IP
    except Exception as e:
        logger.error(f"Error during authentication: {e}", exc_info=True)
        return None  # Error during authentication


async def auth_middleware(app: web.Application, handler):
    """Authentication middleware for aiohttp."""
    async def middleware(request: web.Request):
        authenticated_ip = await authenticate(request)
        if authenticated_ip:
            # Store authenticated IP
            request["authenticated_ip"] = authenticated_ip
            return await handler(request)
        else:
            raise web.HTTPUnauthorized(reason="Unauthorized")
    return middleware
