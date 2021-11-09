import json

import pytest
import socketio
import websockets
import yaml
import os
import pathlib

BASE_PATH = pathlib.Path(os.path.dirname(os.path.realpath(__file__))).parent.parent
DOMAIN_YAML_PATH = os.path.join(BASE_PATH, 'rasa_ai', 'domain.yml')

RASA_SERVER_URL = 'http://localhost:5005/'
FASTAPI_WEBSOCKET_URL = 'ws://localhost:8000/ws'


with open(DOMAIN_YAML_PATH) as f:
    DOMAIN = yaml.load(f.read(), Loader=yaml.FullLoader)


@pytest.mark.asyncio
async def test_orchestrator_to_rasa():
    """
    Test end-to-end data flow from orchestrator to Rasa server.
    """
    async with websockets.connect(FASTAPI_WEBSOCKET_URL) as websocket:
        response = await websocket.recv()
        response = json.loads(response)

        assert response == {'status': 'Connected'}

        await websocket.send(json.dumps({'message': 'Hello', 'lang': 'en'}))

        response = await websocket.recv()
        response = json.loads(response)

        greet_responses = [x['text'] for x in DOMAIN['responses']['utter_greet']]
        assert 'text' in response
        assert len(response) == 1
        assert response['text'] in greet_responses


def test_rasa_to_actions_dialogpt():
    """
    Test invocation of DialoGPT custom action from actions server through Rasa socket.io connection.
    """
    client = socketio.Client()

    client.connect(RASA_SERVER_URL)

    def bot_uttered(data):
        assert len(data) == 1
        assert 'text' in data
        assert isinstance(data['text'], str)

        client.disconnect()

    client.on('bot_uttered', bot_uttered)

    client.emit('user_uttered', data={'message': 'I love red roses'})


def test_rasa_to_actions_forms():
    client = socketio.Client()

    client.connect(RASA_SERVER_URL)

    responses = []

    def bot_uttered(data):
        assert len(data) == 1
        assert 'text' in data
        assert isinstance(data['text'], str)

        responses.append(data['text'])

    client.on('bot_uttered', bot_uttered)

    client.emit('user_uttered', data={'message': 'I want to choose housing'})

    client.sleep(5) # FIX HARDCODE

    ask_specifics_responses = [x['text'] for x in DOMAIN['responses']['utter_ask_specifics']]
    ask_housing_city_responses = [x['text'] for x in DOMAIN['responses']['utter_ask_housing_city']]
    assert responses[0] in ask_specifics_responses
    assert responses[1] in ask_housing_city_responses

    client.disconnect()

# test translation