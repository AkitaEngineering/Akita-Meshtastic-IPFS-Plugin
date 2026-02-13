import ipfshttpclient
import logging
import aiohttp
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)
IPFS_RETRY_COUNT = 3
IPFS_RETRY_DELAY = 2


async def create_ipfs_node() -> Optional[ipfshttpclient.AsyncHTTPClient]:
    """Creates and returns an IPFS client instance."""
    loop = asyncio.get_event_loop()
    for attempt in range(IPFS_RETRY_COUNT):
        try:
            client = await loop.run_in_executor(None, ipfshttpclient.connect)
            logger.info("Connected to IPFS node")
            return client
        except Exception as e:
            logger.error(f"Error connecting to IPFS (attempt {attempt + 1}/{IPFS_RETRY_COUNT}): {e}")
            if attempt < IPFS_RETRY_COUNT - 1:
                await asyncio.sleep(IPFS_RETRY_DELAY)
            else:
                return None
    return None


async def stop_ipfs_node(client: ipfshttpclient.AsyncHTTPClient):
    """Closes the IPFS client connection."""
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(None, client.close)
        logger.info("Disconnected from IPFS node")
    except Exception as e:
        logger.error(f"Error disconnecting from IPFS: {e}", exc_info=True)


async def add_data(client: ipfshttpclient.AsyncHTTPClient, data: bytes, session: aiohttp.ClientSession = None) -> Optional[str]:
    """Adds data to IPFS and returns the CID.

    `session` is accepted for API symmetry with `get_data()` and may be used in future
    implementations that call external gateways.
    """
    loop = asyncio.get_event_loop()
    for attempt in range(IPFS_RETRY_COUNT):
        try:
            res = await loop.run_in_executor(None, client.add, data)
            cid = res['Hash']
            logger.info(f"Added data to IPFS, CID: {cid}")
            return cid
        except Exception as e:
            logger.error(f"Error adding data to IPFS (attempt {attempt + 1}/{IPFS_RETRY_COUNT}): {e}", exc_info=True)
            if attempt < IPFS_RETRY_COUNT - 1:
                await asyncio.sleep(IPFS_RETRY_DELAY)
            else:
                return None
    return None


async def get_data(client: ipfshttpclient.AsyncHTTPClient, cid: str, session: aiohttp.ClientSession) -> Optional[bytes]:
    """Retrieves data from IPFS using the CID."""
    loop = asyncio.get_event_loop()
    for attempt in range(IPFS_RETRY_COUNT):
        try:
            data = await loop.run_in_executor(None, client.cat, cid)
            logger.info(f"Retrieved data for CID {cid}")
            return data
        except Exception as e:
            logger.error(f"Error getting data from IPFS (attempt {attempt + 1}/{IPFS_RETRY_COUNT}): {e}", exc_info=True)
            if attempt < IPFS_RETRY_COUNT - 1:
                await asyncio.sleep(IPFS_RETRY_DELAY)
            else:
                return None
    return None
