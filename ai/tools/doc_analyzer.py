"""文档分析工具"""

DOC_TOOL = {
    "name": "analyze_document",
    "description": "分析文档内容",
    "input_schema": {
        "type": "object",
        "properties": {
            "content": {"type": "string", "description": "文档内容"},
            "task": {"type": "string", "description": "分析任务"}
        },
        "required": ["content"]
    }
}

async def analyze_document(params: dict) -> str:
    content = params.get("content", "")
    task = params.get("task", "summarize")
    return f"文档分析完成 ({len(content)} 字符)"
