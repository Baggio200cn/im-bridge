"""工具集合"""
from .code_executor import execute_code, CODE_TOOL
from .web_search import web_search, SEARCH_TOOL
from .image_gen import generate_image, IMAGE_TOOL
from .doc_analyzer import analyze_document, DOC_TOOL
from .file_handler import handle_file, FILE_TOOL
from .db_query import query_database, DB_TOOL
from .api_caller import call_api, API_TOOL

TOOLS = [CODE_TOOL, SEARCH_TOOL, IMAGE_TOOL, DOC_TOOL, FILE_TOOL, DB_TOOL, API_TOOL]

TOOL_MAP = {
    "execute_code": execute_code,
    "web_search": web_search,
    "generate_image": generate_image,
    "analyze_document": analyze_document,
    "handle_file": handle_file,
    "query_database": query_database,
    "call_api": call_api,
}

async def execute_tool(name: str, params: dict):
    if name in TOOL_MAP:
        return await TOOL_MAP[name](params)
    return f"Unknown tool: {name}"
