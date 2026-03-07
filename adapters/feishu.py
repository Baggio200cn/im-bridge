"""飞书适配器"""
import hashlib
import base64
import json
import logging
from typing import Dict, Any
import httpx
from .base import BaseAdapter
from core.message import Message, Response, Platform, MessageType, User, Attachment
from config.settings import settings

logger = logging.getLogger(__name__)

class FeishuAdapter(BaseAdapter):
    def __init__(self):
        super().__init__()
        self.platform = Platform.FEISHU
        self.base_url = "https://open.feishu.cn/open-apis"
        self.access_token = None

    async def start(self):
        await self._refresh_token()
        self.is_running = True

    async def stop(self):
        self.is_running = False

    async def _refresh_token(self):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/auth/v3/tenant_access_token/internal",
                json={"app_id": settings.feishu.app_id, "app_secret": settings.feishu.app_secret}
            )
            data = resp.json()
            self.access_token = data.get("tenant_access_token")

    async def handle_event(self, event: Dict[str, Any]) -> Dict:
        event_type = event.get("header", {}).get("event_type")
        if event_type == "im.message.receive_v1":
            msg_data = event.get("event", {}).get("message", {})
            sender_data = event.get("event", {}).get("sender", {})
            content = json.loads(msg_data.get("content", "{}"))
            
            message = Message(
                content=content.get("text", ""),
                platform=Platform.FEISHU,
                chat_id=msg_data.get("chat_id", ""),
                sender=User(id=sender_data.get("sender_id", {}).get("user_id", "")),
                id=msg_data.get("message_id", "")
            )
            
            if self.message_handler:
                response = await self.message_handler(message)
                if response:
                    await self.send_message(message.chat_id, response)
        return {"code": 0}

    async def send_message(self, chat_id: str, response: Response):
        if not self.access_token:
            await self._refresh_token()
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.base_url}/im/v1/messages",
                params={"receive_id_type": "chat_id"},
                headers={"Authorization": f"Bearer {self.access_token}"},
                json={"receive_id": chat_id, "msg_type": "text", "content": json.dumps({"text": response.content})}
            )
