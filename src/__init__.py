"""
Things 3 MCP Server

An MCP server that provides access to Things 3, the todo list management application.
This allows LLM clients to read, update, and create new todos in Things 3.
"""

from things3_mcp.applescript_orchestrator import (
    AppleScriptOrchestrator as AppleScriptOrchestrator,
    AppleScriptError as AppleScriptError,
)
from things3_mcp.things3_api import Things3API as Things3API
from things3_mcp.models import (
    Todo as Todo,
    TodoCreate as TodoCreate,
    TodoUpdate as TodoUpdate,
    Project as Project,
    Area as Area,
    Tag as Tag,
    Status as Status,
)

__version__ = "0.1.0"
