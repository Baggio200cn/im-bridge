"""适配器基类"""
from abc import ABC, abstractmethod
from typing import Callable, Optional
from core.message import Message, Response, Platform

class BaseAdapter(ABC):
    def __init__(self):
        self.platform: Platform = None
        self.message_handler: Optional[Callable] = None
        self.is_running = False

    def set_message_handler(self, handler: Callable):
        self.message_handler = handler

    @abstractmethod
    async def start(self):
        pass

    @abstractmethod
    async def stop(self):
        pass

    @abstractmethod
    async def send_message(self, chat_id: str, response: Response):
        pass
