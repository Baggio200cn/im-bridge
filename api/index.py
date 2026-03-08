import os
import json
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

FEISHU_APP_ID = os.getenv('FEISHU_APP_ID', '')
FEISHU_APP_SECRET = os.getenv('FEISHU_APP_SECRET', '')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

@app.api_route("/api", methods=["GET", "POST"])
@app.api_route("/", methods=["GET", "POST"])
async def handler(request: Request):
    if request.method == "GET":
        return {"status": "ok"}
    
    data = await request.json()
    
    # URL验证 - 立即返回
    if data.get('type') == 'url_verification':
        return {"challenge": data.get('challenge', '')}
    
    # 处理消息
    event = data.get('event', {})
    msg = event.get('message', {})
    chat_id = msg.get('chat_id', '')
    content = json.loads(msg.get('content', '{}'))
    text = content.get('text', '')
    
    if text and chat_id:
        # 获取 token
        async with httpx.AsyncClient() as c:
            r = await c.post(
                'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
                json={'app_id': FEISHU_APP_ID, 'app_secret': FEISHU_APP_SECRET}
            )
            token = r.json().get('tenant_access_token')
            
            # 调用 Claude
            r2 = await c.post(
                'https://api.anthropic.com/v1/messages',
                headers={'x-api-key': ANTHROPIC_API_KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'},
                json={'model': 'claude-sonnet-4-20250514', 'max_tokens': 4096, 'messages': [{'role': 'user', 'content': text}]},
                timeout=55.0
            )
            reply = r2.json().get('content', [{}])[0].get('text', 'Error')
            
            # 发送回复
            await c.post(
                'https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id',
                headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
                json={'receive_id': chat_id, 'msg_type': 'text', 'content': json.dumps({'text': reply})}
            )
    
    return {"code": 0}
