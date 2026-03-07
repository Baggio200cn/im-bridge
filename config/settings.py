"""配置管理"""
import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

@dataclass
class ClaudeConfig:
    api_key: str = field(default_factory=lambda: os.getenv('ANTHROPIC_API_KEY', ''))
    model: str = 'claude-sonnet-4-20250514'
    max_tokens: int = 8192

@dataclass
class FeishuConfig:
    app_id: str = field(default_factory=lambda: os.getenv('FEISHU_APP_ID', ''))
    app_secret: str = field(default_factory=lambda: os.getenv('FEISHU_APP_SECRET', ''))
    encrypt_key: str = field(default_factory=lambda: os.getenv('FEISHU_ENCRYPT_KEY', ''))
    verification_token: str = field(default_factory=lambda: os.getenv('FEISHU_VERIFICATION_TOKEN', ''))

@dataclass
class DiscordConfig:
    bot_token: str = field(default_factory=lambda: os.getenv('DISCORD_BOT_TOKEN', ''))
    command_prefix: str = '!'

@dataclass
class Settings:
    claude: ClaudeConfig = field(default_factory=ClaudeConfig)
    feishu: FeishuConfig = field(default_factory=FeishuConfig)
    discord: DiscordConfig = field(default_factory=DiscordConfig)
    debug: bool = field(default_factory=lambda: os.getenv('DEBUG', 'false').lower() == 'true')

settings = Settings()
