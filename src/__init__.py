"""
Things 3 MCP Server

An MCP server that provides access to Things 3, the todo list management application.
This allows LLM clients to read, update, and create new todos in Things 3.
"""

from .applescript_orchestrator import AppleScriptOrchestrator, AppleScriptError
from .things3_api import Things3API
from .models import Todo, TodoCreate, TodoUpdate, Project, Area, Tag, Status
# from .mcp_server import ThingsMCPServer

__version__ = "0.1.0"
