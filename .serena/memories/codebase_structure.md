# Codebase Structure

## Core Source Files (src/)
- `__init__.py` - Package exports and version
- `__main__.py` - Entry point for running as module
- `mcp_server.py` - FastMCP server implementation with tool definitions
- `things3_api.py` - High-level Python API for Things 3 operations
- `applescript_orchestrator.py` - Low-level AppleScript command executor
- `models.py` - Pydantic data models (Todo, Project, Area, Tag, etc.)

## Tests
- `src/tests/` - Unit tests for core components
- `test_*.py` - Integration and manual test files in root

## Configuration
- `pyproject.toml` - Project dependencies and metadata
- `uv.lock` - Locked dependency versions
- `.gitignore` - Git ignore patterns
- `CLAUDE.md` - Development instructions and architecture docs

## Entry Points
- `python -m src.mcp_server` - Main MCP server
- `python -m src` - Alternative entry point
- Various test scripts for development/debugging