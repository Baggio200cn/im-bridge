"""代码执行工具"""
import subprocess
import tempfile
import os

CODE_TOOL = {
    "name": "execute_code",
    "description": "执行代码并返回结果",
    "input_schema": {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "要执行的代码"},
            "language": {"type": "string", "enum": ["python", "javascript", "bash"]}
        },
        "required": ["code", "language"]
    }
}

async def execute_code(params: dict) -> str:
    code = params.get("code", "")
    lang = params.get("language", "python")
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix=get_ext(lang), delete=False) as f:
            f.write(code)
            f.flush()
            cmd = get_cmd(lang, f.name)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            os.unlink(f.name)
            return result.stdout or result.stderr
    except subprocess.TimeoutExpired:
        return "执行超时"
    except Exception as e:
        return f"错误: {e}"

def get_ext(lang):
    return {".py": "python", ".js": "javascript", ".sh": "bash"}.get(lang, ".py")

def get_cmd(lang, path):
    cmds = {"python": ["python3", path], "javascript": ["node", path], "bash": ["bash", path]}
    return cmds.get(lang, ["python3", path])
