# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

**Note:** This project uses `uv` as its package manager.

**Install dependencies:**
```bash
uv sync
```

**Install package in development mode:**
```bash
uv pip install -e .
```

**Activate the virtual environment:**
```bash
source .venv/bin/activate
```

**Start the MCP server:**
```bash
# Using the console script (recommended):
uv run things3-mcp-server

# Or if you have activated the virtual environment:
things3-mcp-server

# Alternative - run as a module:
python -m src.mcp_server

# Or run the package directly:
python -m src
```

**Code formatting and linting:**
```bash
ruff check src/
ruff format src/
```

**Run tests:**
```bash
pytest
pytest src/tests/  # Run all tests
pytest src/tests/test_applescript_orchestrator.py -v  # Run specific test file with verbose output
```

**Run test scripts:**
```bash
# After installing the package in development mode (uv pip install -e .)
python test_read_api.py  # Comprehensive test of all read operations
python test_create_todo.py  # Test todo creation
python debug_create_todo.py  # Debug AppleScript generation
```

**Import pattern:**
```python
# All imports now use the things3_mcp package name
from things3_mcp.things3_api import Things3API
from things3_mcp.models import TodoCreate, Project, Area
from things3_mcp.applescript_orchestrator import AppleScriptOrchestrator
```

## Architecture Overview

This is an MCP (Model Control Protocol) server that bridges LLM clients with the Things 3 macOS application. The architecture follows a layered approach:

```
MCP Client → MCP Server → Things3 API → AppleScript Orchestrator → Things 3 App
```

### Key Layers

1. **MCP Server Handler** (`src/mcp_server.py`): Implements MCP protocol using FastMCP, exposes tools for todo operations, handles request/response flow
2. **Things3 API Layer** (`src/things3_api.py`): High-level Python API providing complete access to Things 3 data via AppleScript commands with data validation
3. **AppleScript Orchestrator** (`src/applescript_orchestrator.py`): Generic AppleScript executor that handles command execution via `osascript`, data type conversion between Python and AppleScript
4. **Data Models** (`src/models.py`): Pydantic models for type safety and validation (Todo, Project, Area, Tag with their respective Create/Update variants)

### MCP Tools Available

The server exposes these tools to MCP clients:

**Read Operations:**
- `get_todo` - Retrieve a specific todo by ID
- `get_all_todos` - Get all todos with optional filtering
- `get_todos_by_list`, `get_todos_by_project`, `get_todos_by_area`, `get_todos_by_tag` - Filter todos by containers
- `get_project`, `get_all_projects`, `get_projects_by_area` - Project operations
- `get_area`, `get_all_areas` - Area operations  
- `get_tag`, `get_all_tags` - Tag operations

**Write Operations:**
- `create_todo` - Create new todos with full property support
- `update_todo` - Update existing todos

### Data Flow Patterns

- **Property Conversion**: API layer handles conversion from AppleScript properties to Pydantic models via parsing methods (`_parse_todo()`, `_parse_project()`, etc.)
- **Date Parsing**: AppleScript date strings are parsed using `python-dateutil` to handle the verbose format (e.g., "Friday, June 20, 2025 at 20:24:26")
- **Error Handling**: AppleScript errors are caught and wrapped as `AppleScriptError` exceptions
- **Entity References**: Related entities use AppleScript references (e.g., "project id ABC123", "area id XYZ789")

## Documentation Resources

- **Things 3 AppleScript Guide**: https://culturedcode.com/things/download/Things3AppleScriptGuide.pdf
  - Official reference for all Things 3 AppleScript commands and properties
  - Contains detailed documentation for creating, reading, updating, and deleting todos, projects, areas, and tags

## Requirements

- macOS with Things 3 application installed
- Python 3.13+
- AppleScript access (`osascript` command available)

### Dependencies

- `fastmcp>=2.8.1` - MCP (Model Control Protocol) implementation
- `python-dateutil>=2.9.0.post0` - Date parsing for AppleScript date formats

### Development Dependencies

- `pytest>=8.3.5` - Testing framework
- `ruff>=0.9.3` - Python linter and formatter
- `rich>=13.9.4` - Rich text formatting for test output

## Configuration

The server runs using STDIO transport by default, which is the standard for MCP clients. The server can be customized by modifying the FastMCP initialization in `src/mcp_server.py`.

## Current Status

The project currently implements:
- ✅ AppleScript orchestrator for executing commands
- ✅ Complete API for todos, projects, areas, and tags (read and write operations)
- ✅ Pydantic models for type safety
- ✅ Comprehensive test suite with 90+ tests covering all operations
- ✅ Fixture-based testing approach with real AppleScript output samples
- ✅ MCP server implementation using FastMCP with all tools exposed

The MCP server is implemented in `src/mcp_server.py` and can be run using the methods described above.

## MCP Server Implementation with FastMCP

This project uses FastMCP (https://gofastmcp.com) to implement the MCP server. FastMCP provides:

### Key Features
- **Tools**: Expose functions as executable capabilities for MCP clients
- **Resources & Templates**: Expose data sources and dynamic content generators
- **Prompts**: Create reusable, parameterized prompt templates
- **Middleware**: Add cross-cutting functionality to inspect, modify, and respond to MCP requests
- **Multiple Transport Protocols**: Support for STDIO, Streamable HTTP, and SSE

### Implementation Guide
When implementing the MCP server:
1. Use FastMCP's decorators to expose the Things3 API methods as tools
2. Implement proper error handling and validation
3. Follow FastMCP's patterns for request/response handling
4. Use middleware for logging and authentication if needed

For detailed FastMCP documentation, see: https://gofastmcp.com/llms.txt

## Testing

The test suite includes:
- **Unit tests** for AppleScript orchestrator (337 lines, comprehensive value conversion and parsing tests)
- **Unit tests** for Things3 API (614 lines, all read operations with mocked AppleScript)
- **Integration tests** (`test_read_api.py` - 281 lines, tests against real Things 3 app)
- **Fixture files** in `tests/fixtures/` containing real AppleScript output for testing parsing logic