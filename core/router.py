"""消息路由器"""
import asyncio
from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
from .message import Message, Response, Session, Platform, MessageType

logger = logging.getLogger(__name__)

class CommandType(Enum):
    CHAT = 'chat'
    IMAGE = 'image'
    CODE = 'code'
    TOOL = 'tool'
    HELP = 'help'
    CLEAR = 'clear'
    STATUS = 'status'
    ADMIN = 'admin'

@dataclass
class Command:
    name: str
    type: CommandType
    description: str
    usage: str
    permission_level: int = 0
    handler: Optional[Callable] = None
    aliases: List[str] = field(default_factory=list)

class MessageRouter:
    def __init__(self):
        self.handlers: Dict[CommandType, Callable] = {}
        self.middlewares: List[Callable] = []
        self.sessions: Dict[str, Session] = {}
        self.commands: Dict[str, Command] = {}
        self._init_commands()

    def _init_commands(self):
        cmds = [
            Command('help', CommandType.HELP, '显示帮助', '/help', 0, aliases=['h']),
            Command('chat', CommandType.CHAT, '对话', '/chat <消息>', 0, aliases=['c']),
            Command('image', CommandType.IMAGE, '图片分析', '/image', 1, aliases=['img']),
            Command('code', CommandType.CODE, '执行代码', '/code <语言>', 2, aliases=['run']),
            Command('clear', CommandType.CLEAR, '清除历史', '/clear', 0),
            Command('status', CommandType.STATUS, '状态', '/status', 0),
        ]
        for cmd in cmds:
            self.commands[cmd.name] = cmd
            for alias in cmd.aliases:
                self.commands[alias] = cmd

    def register_handler(self, cmd_type: CommandType, handler: Callable):
        self.handlers[cmd_type] = handler

    def add_middleware(self, middleware: Callable):
        self.middlewares.append(middleware)

    def get_session(self, message: Message) -> Session:
        sid = f"{message.platform.value}:{message.chat_id}"
        if sid not in self.sessions:
            self.sessions[sid] = Session(id=sid, platform=message.platform)
        return self.sessions[sid]

    def clear_session(self, message: Message):
        sid = f"{message.platform.value}:{message.chat_id}"
        if sid in self.sessions:
            self.sessions[sid].messages = []

    async def route(self, message: Message) -> Response:
        for mw in self.middlewares:
            result = await mw(message)
            if result is False:
                return None
        session = self.get_session(message)
        cmd_type, cmd = self._parse_command(message)
        handler = self.handlers.get(cmd_type)
        if handler:
            return await handler(message, session, cmd)
        return Response(content="未知命令")

    def _parse_command(self, message: Message):
        text = message.content.strip()
        if text.startswith('/'):
            parts = text[1:].split(maxsplit=1)
            cmd_name = parts[0].lower()
            if cmd_name in self.commands:
                return self.commands[cmd_name].type, self.commands[cmd_name]
        if message.attachments:
            return CommandType.IMAGE, self.commands.get('image')
        return CommandType.CHAT, self.commands.get('chat')

    def generate_help(self, level: int = 0) -> str:
        lines = ["**可用命令:**", ""]
        for name, cmd in self.commands.items():
            if name == cmd.name and cmd.permission_level <= level:
                lines.append(f"- `{cmd.usage}` - {cmd.description}")
        return "\n".join(lines)

async def permission_middleware(message: Message) -> bool:
    return True

async def dedup_middleware(message: Message) -> bool:
    return True
