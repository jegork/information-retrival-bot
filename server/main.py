from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from mtranslate import translate
import httpx
import json
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import Dict
import socketio
from bs4 import BeautifulSoup
import requests
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

@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
    manager.set_websocket(websocket)
    await sio.connect(f'http://{os.getenv("RASA_HOST", "localhost")}:5005/')

    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()
            print(data)
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
        response = await client.post(f'http://{os.getenv("RASA_HOST", "localhost")}:5005/webhooks/rest/webhook', json={'sender': sender, 'message': msg})

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

        soup = BeautifulSoup(r.text)

        response_data['image'] = soup.find(class_='picture__image')['src']

    await manager.websocket.send_json(response_data)