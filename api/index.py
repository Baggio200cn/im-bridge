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
    # GET 请求 - 健康检查
    if request.method == "GET":
        return {"status": "ok", "service": "im-bridge"}

    # POST 请求 - 解析 JSON
    try:
        data = await request.json()
    except Exception:
        return {"code": 0}

    # URL 验证 - 飞书验证时立即返回 challenge
    if data.get('type') == 'url_verification':
        return JSONResponse(content={"challenge": data.get('challenge', '')})

    # 处理消息事件
    header = data.get('header', {})
    if header.get('event_type') == 'im.message.receive_v1':
        event = data.get('event', {})
        msg = event.get('message', {})
        chat_id = msg.get('chat_id', '')

        # 解析消息内容
        try:
            content = json.loads(msg.get('content', '{}'))
        except json.JSONDecodeError:
            content = {}

        text = content.get('text', '')

        # 有消息内容时处理
        if text and chat_id:
            try:
                async with httpx.AsyncClient() as client:
                    # 1. 获取飞书 access token
                    token_resp = await client.post(
                        'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
                        json={
                            'app_id': FEISHU_APP_ID,
                            'app_secret': FEISHU_APP_SECRET
                        },
                        timeout=10.0
                    )
                    token = token_resp.json().get('tenant_access_token', '')

                    if not token:
                        return {"code": 0}

                    # 2. 调用 Claude API
                    claude_resp = await client.post(
                        'https://api.anthropic.com/v1/messages',
                        headers={
                            'x-api-key': ANTHROPIC_API_KEY,
                            'anthropic-version': '2023-06-01',
                            'content-type': 'application/json'
                        },
                        json={
                            'model': 'claude-sonnet-4-20250514',
                            'max_tokens': 4096,
                            'messages': [{'role': 'user', 'content': text}]
                        },
                        timeout=55.0
                    )

                    claude_data = claude_resp.json()
                    reply = claude_data.get('content', [{}])[0].get('text', '抱歉，处理失败')

                    # 3. 发送回复到飞书
                    await client.post(
                        'https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id',
                        headers={
                            'Authorization': f'Bearer {token}',
                            'Content-Type': 'application/json'
                        },
                        json={
                            'receive_id': chat_id,
                            'msg_type': 'text',
                            'content': json.dumps({'text': reply})
                        },
                        timeout=10.0
                    )

            except Exception:
                pass

    return {"code": 0}
