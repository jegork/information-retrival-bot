import json
import os
import httpx
import requests
import socketio
from bs4 import BeautifulSoup
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from mtranslate import translate
from pydantic import BaseModel
from starlette.responses import FileResponse


class Message(BaseModel):
    text: str
    sender: str


class Manager():
    def __init__(self):
        self.websocket = None
        self.lang = None
        self.user_id = None

    def set_websocket(self, websocket: WebSocket):
        self.websocket = websocket

    def set_lang(self, lang: str):
        self.lang = lang

    def set_user_id(self, user_id: int):
        self.user_id = user_id


app = FastAPI()
manager = Manager()
sio = socketio.AsyncClient()

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
async def websocket_endpoint(websocket: WebSocket):
    manager.set_websocket(websocket)
    await sio.connect(f'http://{os.getenv("RASA_HOST", "localhost")}:5005/')

    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()
            manager.set_lang(data['lang'])
            if data['lang'] != 'en':
                text = translate(data['message'], 'en', data['lang'])
            else:
                text = data['message']

            await sio.emit("user_uttered", data={'message': text})
    except WebSocketDisconnect:
        await sio.disconnect()
        print('User disconnected')


async def request(sender: str, msg: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(f'http://{os.getenv("RASA_HOST", "localhost")}:5005/webhooks/rest/webhook',
                                     json={'sender': sender, 'message': msg})

    return json.loads(response.text)[0]


@app.post('/chat/{lang}')
async def chat(lang: str, message: Message):
    if lang != 'en':
        text = translate(message.text, 'en', lang)

        response = await request(message.sender, text)

        return {'text': translate(response['text'], lang, 'en')}
    else:
        text = message.text

        response = await request(message.sender, text)

        return {'text': response['text']}


@sio.on('connect')
def connect():
    print('Rasa socket.io connected')


@sio.on('bot_uttered')
async def bot_uttered(msg):
    response_data = {}

    if 'text' in msg:
        if manager.lang != 'en':
            text = translate(msg['text'], manager.lang, 'en')
        else:
            text = msg['text']

        response_data['text'] = text

    if 'attachment' in msg:
        r = requests.get(msg['attachment'])

        soup = BeautifulSoup(r.text, features='html.parser')
        ad_viewport = soup.find(class_='carrousel__viewport')

        if ad_viewport is not None:
            response_data['image'] = ad_viewport.find(class_='picture__image')['src']

    await manager.websocket.send_json(response_data)
