#from fastapi.logger import logger
import os
from typing import List
import logging

import requests
import socketio
from bs4 import BeautifulSoup
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from mtranslate import translate
from pydantic import BaseModel
from starlette.responses import FileResponse

RASA_URL = f'http://{os.getenv("RASA_HOST", "localhost")}:5005/'

logger = logging.getLogger(__name__)


class Message(BaseModel):
    text: str
    sender: str


class Connection:
    def __init__(self, websocket: WebSocket, socketio: socketio.AsyncClient):
        self.websocket = websocket
        self.socketio = socketio
        self.lang = 'en'

        self.socketio.on('bot_uttered', self.bot_uttered)

    async def connect(self) -> bool:
        await self.websocket.accept()
        await self.websocket.send_json({'status': 'Connected'})

        try:
            await self.socketio.connect(RASA_URL)
        except socketio.exceptions.ConnectionError:
            await self.websocket.close()
            return False

        return True

    async def bot_uttered(self, data):
        response_data = {}

        if 'text' in data:
            if self.lang != 'en':
                text = translate(data['text'], self.lang, 'en')
            else:
                text = data['text']

            response_data['text'] = text

        if 'title' in data:
            if self.lang != 'en':
                text = translate(data['title'], self.lang, 'en')
            else:
                text = data['title']

            response_data['title'] = text

        if 'link' in data:
            response_data['link'] = data['link']

            r = requests.get(data['link'])

            soup = BeautifulSoup(r.text, features='html.parser')
            ad_viewport = soup.find(class_='carrousel__viewport')

            if ad_viewport is not None:
                response_data['image'] = ad_viewport.find(class_='picture__image')['src']

        await self.websocket.send_json(response_data)


class ConnectionManager:
    def __init__(self):
        self.connections: List[Connection] = []

    async def add_connection(self, websocket: WebSocket, socketio: socketio.AsyncClient) -> int:
        new_connection = Connection(websocket=websocket, socketio=socketio)
        self.connections.append(new_connection)

        return len(self.connections) - 1

    def set_language(self, connection_id: int, lang: str):
        self.connections[connection_id].lang = lang

    async def connect(self, connection_id: int) -> bool:
        return await self.connections[connection_id].connect()


app = FastAPI()
connection_manager = ConnectionManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get('/')
def main_page():
    return FileResponse('index.html')


@app.websocket('/ws')
async def websocket(websocket: WebSocket):
    connection_id = await connection_manager.add_connection(websocket, socketio.AsyncClient())
    connected = await connection_manager.connect(connection_id)

    if connected:
        try:
            while True:
                data = await connection_manager.connections[connection_id].websocket.receive_json()
                connection_manager.set_language(connection_id, data['lang'])

                if data['lang'] != 'en':
                    text = translate(data['message'], 'en', data['lang'])
                else:
                    text = data['message']

                await connection_manager.connections[connection_id].socketio.emit("user_uttered",
                                                                                  data={'message': text})

        except WebSocketDisconnect:
            await connection_manager.connections[connection_id].socketio.disconnect()            
    else:
        logger.error('Failed to establish connection!')
