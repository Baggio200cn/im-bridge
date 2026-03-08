import os
import json
import hashlib
import base64
import time
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

FEISHU_APP_ID = os.getenv('FEISHU_APP_ID', '')
FEISHU_APP_SECRET = os.getenv('FEISHU_APP_SECRET', '')
FEISHU_ENCRYPT_KEY = os.getenv('FEISHU_ENCRYPT_KEY', '')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-20250514')

_token_cache = {'token': None, 'expires': 0}


async def get_tenant_token():
    if _token_cache['token'] and time.time() < _token_cache['expires']:
        return _token_cache['token']
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
            json={'app_id': FEISHU_APP_ID, 'app_secret': FEISHU_APP_SECRET}
        )
        data = resp.json()
        if data.get('code') == 0:
            _token_cache['token'] = data['tenant_access_token']
            _token_cache['expires'] = time.time() + data['expire'] - 60
            return _token_cache['token']
    return None


async def call_claude(message: str) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key': ANTHROPIC_API_KEY,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json'
            },
            json={
                'model': CLAUDE_MODEL,
                'max_tokens': 4096,
                'messages': [{'role': 'user', 'content': message}]
            }
        )
        data = resp.json()
        if 'content' in data and len(data['content']) > 0:
            return data['content'][0]['text']
        return f"Error: {data}"


async def send_feishu_message(chat_id: str, text: str):
    token = await get_tenant_token()
    if not token:
        return
    async with httpx.AsyncClient() as client:
        await client.post(
            'https://open.feishu.cn/open-apis/im/v1/messages',
            params={'receive_id_type': 'chat_id'},
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            },
            json={
                'receive_id': chat_id,
                'msg_type': 'text',
                'content': json.dumps({'text': text})
            }
        )


@app.get("/")
async def root():
    return {"status": "ok", "service": "im-bridge"}


@app.get("/api")
async def api_root():
    return {"status": "ok", "service": "im-bridge"}


@app.post("/api")
@app.post("/webhook/feishu")
@app.post("/api/webhook/feishu")
async def feishu_webhook(request: Request):
    body = await request.body()
    data = json.loads(body)

    if data.get('type') == 'url_verification':
        return JSONResponse(content={"challenge": data.get('challenge', '')})

    if 'encrypt' in data and FEISHU_ENCRYPT_KEY:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        key = hashlib.sha256(FEISHU_ENCRYPT_KEY.encode()).digest()
        encrypted = base64.b64decode(data['encrypt'])
        cipher = Cipher(algorithms.AES(key), modes.CBC(encrypted[:16]), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(encrypted[16:]) + decryptor.finalize()
        data = json.loads(decrypted[:-decrypted[-1]].decode())

    event = data.get('event', {})
    message_data = event.get('message', {})
    chat_id = message_data.get('chat_id', '')
    content = json.loads(message_data.get('content', '{}'))
    text = content.get('text', '')

    if text and chat_id:
        reply = await call_claude(text)
        await send_feishu_message(chat_id, reply)

    return JSONResponse(content={"code": 0})
