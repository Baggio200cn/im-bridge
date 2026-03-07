"""消息模型定义"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import uuid

class Platform(Enum):
    FEISHU = 'feishu'
    DISCORD = 'discord'
    SLACK = 'slack'
    WECHAT = 'wechat'
    TELEGRAM = 'telegram'

class MessageType(Enum):
    TEXT = 'text'
    IMAGE = 'image'
    FILE = 'file'
    AUDIO = 'audio'
    VIDEO = 'video'
    CARD = 'card'
    MIXED = 'mixed'

@dataclass
class User:
    id: str
    name: str = ''
    avatar: str = ''
    email: str = ''
    permission_level: int = 0

@dataclass
class Attachment:
    type: str
    url: str = ''
    data: bytes = None
    filename: str = ''
    mime_type: str = ''

@dataclass
class Message:
    content: str
    platform: Platform
    chat_id: str
    sender: Optional[User] = None
    type: MessageType = MessageType.TEXT
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    attachments: List[Attachment] = field(default_factory=list)
    reply_to: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Response:
    content: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    attachments: List[Attachment] = field(default_factory=list)
    model: str = ''
    usage: Dict[str, int] = field(default_factory=dict)
    tool_calls: List[Dict] = field(default_factory=list)

@dataclass
class Session:
    id: str
    platform: Platform
    messages: List[Dict[str, Any]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
