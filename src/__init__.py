"""
Things 3 MCP Server

An MCP server that provides access to Things 3, the todo list management application.
This allows LLM clients to read, update, and create new todos in Things 3.
"""

from .applescript_orchestrator import (
    AppleScriptOrchestrator as AppleScriptOrchestrator,
    AppleScriptError as AppleScriptError,
)
from .things3_api import Things3API as Things3API
from .models import (
    Todo as Todo,
    TodoCreate as TodoCreate,
    TodoUpdate as TodoUpdate,
    Project as Project,
    Area as Area,
    Tag as Tag,
    Status as Status,
)
from .mcp_server import mcp as mcp

__version__ = "0.1.0"
