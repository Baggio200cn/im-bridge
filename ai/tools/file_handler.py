"""文件处理工具"""
import os

FILE_TOOL = {
    "name": "handle_file",
    "description": "读写文件",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["read", "write", "list"]},
            "path": {"type": "string"},
            "content": {"type": "string"}
        },
        "required": ["action", "path"]
    }
}

async def handle_file(params: dict) -> str:
    action = params.get("action")
    path = params.get("path", "")
    
    if action == "read":
        if os.path.exists(path):
            with open(path, 'r') as f:
                return f.read()
        return "文件不存在"
    elif action == "write":
        with open(path, 'w') as f:
            f.write(params.get("content", ""))
        return "写入成功"
    elif action == "list":
        if os.path.isdir(path):
            return "\n".join(os.listdir(path))
        return "不是目录"
    return "未知操作"
