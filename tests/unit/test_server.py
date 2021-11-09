import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from server.main import app, Connection, ConnectionManager
import pathlib
import os

BASE_PATH = pathlib.Path(os.path.dirname(os.path.realpath(__file__))).parent.parent

client = TestClient(app)


def test_websocket_1():
    """
    Test connection to orchestrator through WebSocket connection.
    Should respond with { "status": "connected" } and successful disconnect code (1000).
    """
    with client.websocket_connect('/ws') as websocket:
        data = websocket.receive_json()
        assert data == {'status': 'Connected'}

        response = websocket.receive()
        assert response['code'] == 1000


def test_websocket_2():
    response = client.get('/ws')
    assert response.status_code == 404


def test_index_1():
    """
    Test that root outputs an index.html file.
    """
    index_path = os.path.join(BASE_PATH, 'server', 'index.html')
    response = client.get('/')

    with open(index_path) as f:
        html = f.read()
    assert response.text == html
    assert response.status_code == 200


def test_index_2():
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect('/') as websocket:
            websocket.receive_json()

# TODO: Test class Connection
# TODO: Test class ConnectionManager
