"""API调用工具"""
import httpx

API_TOOL = {
    "name": "call_api",
    "description": "调用外部API",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "method": {"type": "string", "enum": ["GET", "POST"]},
            "data": {"type": "object"}
        },
        "required": ["url"]
    }
}

async def call_api(params: dict) -> str:
    url = params.get("url", "")
    method = params.get("method", "GET")
    data = params.get("data", {})
    
    try:
        async with httpx.AsyncClient() as client:
            if method == "GET":
                resp = await client.get(url, timeout=30)
            else:
                resp = await client.post(url, json=data, timeout=30)
            return resp.text[:1000]
    except Exception as e:
        return f"API调用错误: {e}"
