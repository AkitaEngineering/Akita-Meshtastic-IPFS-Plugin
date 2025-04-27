import ipfshttpclient
import logging
import aiohttp
from typing import Optional

logger = logging.getLogger(__name__)
IPFS_RETRY_COUNT = 3
IPFS_RETRY_DELAY = 2


async def create_ipfs_node() -> Optional[ipfshttpclient.AsyncHTTPClient]:
    """Creates and returns an IPFS client instance."""
    for attempt in range(IPFS_RETRY_COUNT):
        try:
            client = ipfshttpclient.connect()  # Connect to local node
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
    try:
        client.close()
        logger.info("Disconnected from IPFS node")
    except Exception as e:
        logger.error(f"Error disconnecting from IPFS: {e}", exc_info=True)


async def add_data(client: ipfshttpclient.AsyncHTTPClient, data: bytes) -> Optional[str]:
    """Adds data to IPFS and returns the CID."""
    for attempt in range(IPFS_RETRY_COUNT):
        try:
            res = client.add(data)
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
    for attempt in range(IPFS_RETRY_COUNT):
        try:
            data = client.cat(cid)
            logger.info(f"Retrieved data for CID {cid}")
            return data
        except Exception as e:
            logger.error(f"Error getting data from IPFS (attempt {attempt + 1}/{IPFS_RETRY_COUNT}): {e}", exc_info=True)
            if attempt < IPFS_RETRY_COUNT - 1:
                await asyncio.sleep(IPFS_RETRY_DELAY)
            else:
                return None
    return None
