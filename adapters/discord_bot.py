"""Discord适配器"""
import logging
import discord
from discord.ext import commands
from .base import BaseAdapter
from core.message import Message, Response, Platform, User, Attachment
from config.settings import settings

logger = logging.getLogger(__name__)

class DiscordAdapter(BaseAdapter):
    def __init__(self):
        super().__init__()
        self.platform = Platform.DISCORD
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix=settings.discord.command_prefix, intents=intents)
        self._setup_events()

    def _setup_events(self):
        @self.bot.event
        async def on_ready():
            logger.info(f"Discord bot logged in as {self.bot.user}")

        @self.bot.event
        async def on_message(msg):
            if msg.author.bot:
                return
            attachments = [Attachment(type="image", url=a.url) for a in msg.attachments if a.content_type and a.content_type.startswith("image")]
            message = Message(
                content=msg.content,
                platform=Platform.DISCORD,
                chat_id=str(msg.channel.id),
                sender=User(id=str(msg.author.id), name=msg.author.name),
                attachments=attachments
            )
            if self.message_handler:
                response = await self.message_handler(message)
                if response:
                    await self.send_message(str(msg.channel.id), response)

    async def start(self):
        self.is_running = True
        await self.bot.start(settings.discord.bot_token)

    async def stop(self):
        self.is_running = False
        await self.bot.close()

    async def send_message(self, chat_id: str, response: Response):
        channel = self.bot.get_channel(int(chat_id))
        if channel:
            if len(response.content) > 2000:
                for i in range(0, len(response.content), 2000):
                    await channel.send(response.content[i:i+2000])
            else:
                await channel.send(response.content)
