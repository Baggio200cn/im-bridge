from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request

FEISHU_APP_ID = os.getenv('FEISHU_APP_ID', '')
FEISHU_APP_SECRET = os.getenv('FEISHU_APP_SECRET', '')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok", "service": "im-bridge"}).encode())

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body)
        except:
            self._respond({"code": 0})
            return

        # URL 验证
        if data.get('type') == 'url_verification':
            self._respond({"challenge": data.get('challenge', '')})
            return

        # 处理消息
        header = data.get('header', {})
        if header.get('event_type') == 'im.message.receive_v1':
            event = data.get('event', {})
            msg = event.get('message', {})
            chat_id = msg.get('chat_id', '')
            
            try:
                content = json.loads(msg.get('content', '{}'))
            except:
                content = {}
            
            text = content.get('text', '')

            if text and chat_id:
                try:
                    # 获取飞书 token
                    token = self._get_feishu_token()
                    if token:
                        # 调用 Claude
                        reply = self._call_claude(text)
                        # 发送回复
                        self._send_feishu_message(token, chat_id, reply)
                except:
                    pass

        self._respond({"code": 0})

    def _respond(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _get_feishu_token(self):
        req = urllib.request.Request(
            'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
            data=json.dumps({'app_id': FEISHU_APP_ID, 'app_secret': FEISHU_APP_SECRET}).encode(),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read()).get('tenant_access_token', '')

    def _call_claude(self, text):
        req = urllib.request.Request(
            'https://api.anthropic.com/v1/messages',
            data=json.dumps({
                'model': 'claude-sonnet-4-20250514',
                'max_tokens': 4096,
                'messages': [{'role': 'user', 'content': text}]
            }).encode(),
            headers={
                'Content-Type': 'application/json',
                'x-api-key': ANTHROPIC_API_KEY,
                'anthropic-version': '2023-06-01'
            }
        )
        with urllib.request.urlopen(req, timeout=55) as resp:
            data = json.loads(resp.read())
            return data.get('content', [{}])[0].get('text', '处理失败')

    def _send_feishu_message(self, token, chat_id, text):
        req = urllib.request.Request(
            'https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id',
            data=json.dumps({
                'receive_id': chat_id,
                'msg_type': 'text',
                'content': json.dumps({'text': text})
            }).encode(),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
        )
        urllib.request.urlopen(req, timeout=10)
