import asyncio
import pytest
import sys
import os

from types import SimpleNamespace

# Ensure the gateway/src directory is on sys.path so we can import `main` as a module
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
import types
# Provide a dummy ipfshttpclient module for test imports (avoid requiring external deps)
sys.modules.setdefault('ipfshttpclient', types.ModuleType('ipfshttpclient'))
sys.modules.setdefault('aiohttp', types.ModuleType('aiohttp'))
sys.modules.setdefault('socketio', types.ModuleType('socketio'))
sys.modules.setdefault('meshtastic', types.ModuleType('meshtastic'))
sys.modules['ipfshttpclient'].AsyncHTTPClient = object
sys.modules['aiohttp'].ClientSession = object
setattr(sys.modules['meshtastic'], 'SerialInterface', object)
setattr(sys.modules['meshtastic'], 'MeshInterface', object)
setattr(sys.modules['aiohttp'], 'web', types.SimpleNamespace(Response=lambda *a, **k: None, Request=object))
setattr(sys.modules['aiohttp'].web, 'Application', object)
class _DummyAsyncServer:
    def __init__(self, *args, **kwargs):
        pass

    def attach(self, app):
        pass

    async def emit(self, *args, **kwargs):
        pass

    def on(self, *args, **kwargs):
        def _decorator(f):
            return f
        return _decorator

setattr(sys.modules['socketio'], 'AsyncServer', _DummyAsyncServer)

import main as gateway_main


class DummySio:
    def __init__(self):
        self.emits = []

    async def emit(self, event, data):
        self.emits.append((event, data))


class DummyMeshtasticConn:
    def __init__(self):
        self.sent = []

    def send_message(self, message, destination_node=None, port=None):
        # synchronous method to match meshtastic_comm.send_message expectations
        self.sent.append((message, destination_node, port))


def test_handle_meshtastic_message_store(monkeypatch):
    # Simulate receiving data (not a CID) -> should call add_data and send CID back
    ipfs_node = object()
    sio = DummySio()
    meshtastic = DummyMeshtasticConn()

    # Mock ipfs_comm.add_data
    async def fake_add(node, data, session=None):
        return "QmFakeCID"

    monkeypatch.setattr(gateway_main.ipfs_comm, 'add_data', fake_add)
    # create a fake message object
    payload = b'hello world'
    msg = SimpleNamespace(decoded={'portnum': gateway_main.config.IPFS_PORT, 'payload': payload}, from_id=123)

    asyncio.run(gateway_main.handle_meshtastic_message(ipfs_node, meshtastic, sio, None, msg))

    # verify meshtastic send_message was invoked with CID
    assert len(meshtastic.sent) == 1
    sent_cid, dest, port = meshtastic.sent[0]
    assert sent_cid == 'QmFakeCID'
    assert dest == 123
    assert port == gateway_main.config.IPFS_PORT


def test_handle_meshtastic_message_retrieve(monkeypatch):
    # Simulate receiving a CID -> should call get_data and send data back
    ipfs_node = object()
    sio = DummySio()
    meshtastic = DummyMeshtasticConn()

    # Mock ipfs_comm.get_data
    async def fake_get(node, cid, session=None):
        return b'retrieved-data'

    monkeypatch.setattr(gateway_main.ipfs_comm, 'get_data', fake_get)

    cid_str = 'x' * gateway_main.config.CID_LENGTH
    payload = cid_str.encode('utf-8')
    msg = SimpleNamespace(decoded={'portnum': gateway_main.config.IPFS_PORT, 'payload': payload}, from_id=321)

    asyncio.run(gateway_main.handle_meshtastic_message(ipfs_node, meshtastic, sio, None, msg))

    # verify meshtastic send_message was invoked with data
    assert len(meshtastic.sent) == 1
    sent_data, dest, port = meshtastic.sent[0]
    assert sent_data == 'retrieved-data'
    assert dest == 321
    assert port == gateway_main.config.IPFS_PORT
