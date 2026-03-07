"""IM Bridge - 主入口"""
import asyncio
import logging
import signal
from typing import List

from config.settings import settings
from core.router import MessageRouter, CommandType, permission_middleware, dedup_middleware
from core.message import Message, Response
from adapters.base import BaseAdapter
from adapters.feishu import FeishuAdapter
from adapters.discord_bot import DiscordAdapter
from ai.claude_handler import ClaudeHandler
from storage.database import Database, SessionStore, MessageStore

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IMBridge:
    def __init__(self):
        self.router = MessageRouter()
        self.claude = ClaudeHandler()
        self.adapters: List[BaseAdapter] = []
        self.db = Database()
        self.session_store = SessionStore(self.db)
        self.message_store = MessageStore(self.db)
        self._shutdown = asyncio.Event()

    async def setup(self):
        logger.info("正在初始化 IM Bridge...")
        self.router.add_middleware(dedup_middleware)
        self.router.add_middleware(permission_middleware)
        
        self.router.register_handler(CommandType.CHAT, self._handle_chat)
        self.router.register_handler(CommandType.IMAGE, self._handle_image)
        self.router.register_handler(CommandType.CODE, self._handle_code)
        self.router.register_handler(CommandType.TOOL, self._handle_tool)
        self.router.register_handler(CommandType.HELP, self._handle_help)
        self.router.register_handler(CommandType.CLEAR, self._handle_clear)
        self.router.register_handler(CommandType.STATUS, self._handle_status)

        if settings.feishu.app_id:
            adapter = FeishuAdapter()
            adapter.set_message_handler(self._on_message)
            self.adapters.append(adapter)
            
        if settings.discord.bot_token:
            adapter = DiscordAdapter()
            adapter.set_message_handler(self._on_message)
            self.adapters.append(adapter)

    async def start(self):
        logger.info("正在启动 IM Bridge...")
        for adapter in self.adapters:
            await adapter.start()
        logger.info("IM Bridge 已启动!")
        await self._shutdown.wait()

    async def stop(self):
        for adapter in self.adapters:
            await adapter.stop()
        logger.info("IM Bridge 已停止")

    async def _on_message(self, message: Message) -> Response:
        return await self.router.route(message)

    async def _handle_chat(self, message, session, command): return await self.claude.chat(message, session, command)
    async def _handle_image(self, message, session, command): return await self.claude.analyze_image(message, session, command)
    async def _handle_code(self, message, session, command): return await self.claude.execute_code(message, session, command)
    async def _handle_tool(self, message, session, command): return await self.claude.call_tool(message, session, command)
    async def _handle_help(self, message, session, command): return Response(content=self.router.generate_help(0))
    async def _handle_clear(self, message, session, command): self.router.clear_session(message); return Response(content="已清除")
    async def _handle_status(self, message, session, command): return Response(content=f"运行中，{len(self.adapters)}个适配器")

    def shutdown(self): self._shutdown.set()

async def main():
    bridge = IMBridge()
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, bridge.shutdown)
    try:
        await bridge.setup()
        await bridge.start()
    finally:
        await bridge.stop()

if __name__ == '__main__':
    asyncio.run(main())
