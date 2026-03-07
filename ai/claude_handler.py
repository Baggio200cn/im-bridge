"""Claude AI 处理器"""
import logging
from typing import List, Dict, Any, Optional
import anthropic
from core.message import Message, Response, Session
from core.router import Command
from config.settings import settings
from .tools import TOOLS, execute_tool

logger = logging.getLogger(__name__)

class ClaudeHandler:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.claude.api_key)
        self.model = settings.claude.model
        self.max_tokens = settings.claude.max_tokens
        self.system_prompt = """你是一个智能助手，可以帮助用户完成各种任务。
你可以使用以下工具：代码执行、网页搜索、图片生成、文档分析等。
请用简洁专业的方式回答问题。"""

    async def chat(self, message: Message, session: Session, command: Command) -> Response:
        session.messages.append({"role": "user", "content": message.content})
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=self.system_prompt,
            messages=session.messages,
            tools=TOOLS
        )
        
        # Handle tool use
        tool_calls = []
        final_content = ""
        
        for block in response.content:
            if block.type == "text":
                final_content += block.text
            elif block.type == "tool_use":
                tool_result = await execute_tool(block.name, block.input)
                tool_calls.append({"name": block.name, "input": block.input, "result": tool_result})
                
                # Continue conversation with tool result
                session.messages.append({"role": "assistant", "content": response.content})
                session.messages.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": block.id, "content": str(tool_result)}]})
                
                follow_up = self.client.messages.create(
                    model=self.model, max_tokens=self.max_tokens,
                    system=self.system_prompt, messages=session.messages, tools=TOOLS
                )
                for b in follow_up.content:
                    if b.type == "text":
                        final_content += b.text
        
        session.messages.append({"role": "assistant", "content": final_content})
        
        return Response(
            content=final_content,
            model=self.model,
            usage={"input": response.usage.input_tokens, "output": response.usage.output_tokens},
            tool_calls=tool_calls
        )

    async def analyze_image(self, message: Message, session: Session, command: Command) -> Response:
        if not message.attachments:
            return Response(content="请提供图片")
        
        content = [{"type": "text", "text": message.content or "请描述这张图片"}]
        for att in message.attachments:
            if att.url:
                content.append({"type": "image", "source": {"type": "url", "url": att.url}})
        
        response = self.client.messages.create(
            model=self.model, max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": content}]
        )
        return Response(content=response.content[0].text, model=self.model)

    async def execute_code(self, message: Message, session: Session, command: Command) -> Response:
        from .tools.code_executor import execute_code
        result = await execute_code({"code": message.content, "language": "python"})
        return Response(content=f"```\n{result}\n```")

    async def call_tool(self, message: Message, session: Session, command: Command) -> Response:
        parts = message.content.split(maxsplit=1)
        tool_name = parts[0] if parts else ""
        tool_input = parts[1] if len(parts) > 1 else ""
        result = await execute_tool(tool_name, {"query": tool_input})
        return Response(content=str(result))
