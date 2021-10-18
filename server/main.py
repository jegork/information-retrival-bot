from fastapi import FastAPI
from mtranslate import translate
import httpx
import asyncio
import json
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os

class Message(BaseModel):
    text: str
    sender: str

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {'Hello': 'world'}

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