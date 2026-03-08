"""飞书长连接模式 - 独立启动脚本"""
import os
import json
import logging
import httpx
import lark_oapi as lark
from lark_oapi.api.im.v1 import *
from dotenv import load_dotenv

load_dotenv()

# 配置
FEISHU_APP_ID = os.getenv('FEISHU_APP_ID', '')
FEISHU_APP_SECRET = os.getenv('FEISHU_APP_SECRET', '')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 Lark 客户端
client = lark.Client.builder() \
    .app_id(FEISHU_APP_ID) \
    .app_secret(FEISHU_APP_SECRET) \
    .log_level(lark.LogLevel.DEBUG if DEBUG else lark.LogLevel.INFO) \
    .build()


def call_claude(text: str) -> str:
    """调用 Claude API"""
    try:
        with httpx.Client(timeout=60) as http_client:
            resp = http_client.post(
                'https://api.anthropic.com/v1/messages',
                headers={
                    'Content-Type': 'application/json',
                    'x-api-key': ANTHROPIC_API_KEY,
                    'anthropic-version': '2023-06-01'
                },
                json={
                    'model': 'claude-sonnet-4-20250514',
                    'max_tokens': 4096,
                    'messages': [{'role': 'user', 'content': text}]
                }
            )
            data = resp.json()
            return data.get('content', [{}])[0].get('text', '处理失败')
    except Exception as e:
        logger.error(f"调用 Claude 失败: {e}")
        return f"调用失败: {e}"


def send_message(chat_id: str, text: str):
    """发送飞书消息"""
    request = CreateMessageRequest.builder() \
        .receive_id_type("chat_id") \
        .request_body(CreateMessageRequestBody.builder()
            .receive_id(chat_id)
            .msg_type("text")
            .content(json.dumps({"text": text}))
            .build()) \
        .build()

    resp = client.im.v1.message.create(request)
    if not resp.success():
        logger.error(f"发送失败: {resp.code} - {resp.msg}")
    else:
        logger.info("消息已发送")


def handle_message(data) -> None:
    """处理收到的消息"""
    try:
        event = data.event
        message = event.message
        content = json.loads(message.content or "{}")
        text = content.get("text", "")
        chat_id = message.chat_id

        if not text or not chat_id:
            return

        logger.info(f"收到: {text[:50]}...")

        # 调用 Claude 并回复
        reply = call_claude(text)
        send_message(chat_id, reply)

    except Exception as e:
        logger.error(f"处理消息失败: {e}")


def main():
    """启动长连接"""
    logger.info("=" * 50)
    logger.info("IM Bridge 飞书长连接模式")
    logger.info("=" * 50)

    if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
        logger.error("请设置 FEISHU_APP_ID 和 FEISHU_APP_SECRET 环境变量")
        return

    if not ANTHROPIC_API_KEY:
        logger.error("请设置 ANTHROPIC_API_KEY 环境变量")
        return

    # 创建事件处理器
    event_handler = lark.EventDispatcherHandler.builder("", "") \
        .register_p2_im_message_receive_v1(handle_message) \
        .build()

    # 创建并启动 WebSocket 客户端
    ws_client = lark.ws.Client(
        FEISHU_APP_ID,
        FEISHU_APP_SECRET,
        event_handler=event_handler,
        log_level=lark.LogLevel.DEBUG if DEBUG else lark.LogLevel.INFO
    )

    logger.info("正在连接飞书服务器...")
    logger.info("连接成功后，在飞书中发送消息即可收到 Claude 回复")
    logger.info("按 Ctrl+C 停止")

    ws_client.start()


if __name__ == '__main__':
    main()
