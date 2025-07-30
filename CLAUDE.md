# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Control Protocol) server that provides bidirectional integration with the Things 3 macOS application. It enables LLM clients to interact with Things 3 through AppleScript, supporting read and write operations for todos, projects, areas, and tags.

## Common Development Commands

### Environment Setup
Always run python code with uv run
```
uv run python ...
uv run pytest ...
uv run mypy src
```

### Running the Server
```bash
uv run things3-mcp-server
```

### Code Quality and Testing
```bash
# Format and lint code
ruff format src/
ruff check src/

# Run all tests
pytest

# Run specific test file with verbose output
pytest src/tests/test_things3_api.py -v

# Run integration tests (requires Things 3 app)
python test_read_api.py
```

## Architecture Overview

**Layered Architecture** with clear separation:

1. **MCP Server Layer** (`src/things3/mcp_server.py`)
   - FastMCP-based server with tool definitions
   - Async handlers for MCP protocol

2. **API Layer** (`src/things3/things3_api.py`)
   - High-level Python interface for Things 3 operations
   - Handles data validation and orchestration calls

3. **Orchestrator Layer** (`src/things3/orchestrator.py`)
   - Low-level AppleScript command execution
   - Data conversion between Python and AppleScript

4. **Data Models** (`src/things3/models.py`)
   - Pydantic models for type safety and validation
   - Separate models for read operations (Todo, Project) and write operations (TodoCreate, TodoUpdate)

5. **AppleScript System** (`src/applescript/`)
   - Core execution engine (`core.py`)
   - Command builders (`builders.py`)
   - Data parsers (`parsers.py`)
   - Type converters (`converters.py`)

## Key Design Patterns

- **Command Pattern**: AppleScript operations encapsulated as commands
- **Factory Pattern**: Parsers create appropriate model instances from AppleScript data
- **Strategy Pattern**: Different parsers for different AppleScript data types
- **Layered Error Handling**: Custom exception hierarchy with graceful fallbacks

## Development Guidelines

### Data Flow Pattern
```
MCP Client ↔ FastMCP Server ↔ Things3API ↔ Orchestrator ↔ AppleScript ↔ Things 3
```

### Code Style Conventions
- Use Pydantic models for all data validation
- Handle missing/optional values with `None` defaults
- Parse AppleScript dates using `python-dateutil`
- Use logging for debugging AppleScript execution
- Maintain async/await patterns for MCP tools
- Follow existing naming conventions (snake_case for Python, camelCase for AppleScript properties)

### Testing Strategy
- Unit tests in `src/tests/` with mocked AppleScript calls
- Integration tests with `test_*.py` files that require real Things 3 app
- Use pytest fixtures for common test data
- Test both success and error conditions

## Important Requirements

- **macOS only**: Requires macOS with Things 3 app installed
- **Python 3.13+**: Uses modern Python features
- **AppleScript permissions**: Needs accessibility permissions for Things 3 automation
- **Package manager**: Uses `uv` for dependency management

## Entry Points and Module Structure

- Main server: `python -m src.things3.mcp_server`
- Package entry: `python -m src`
- The `src/` directory contains two main packages:
  - `things3/` - Things 3 specific functionality
  - `applescript/` - Generic AppleScript utilities

## Error Handling Strategy

- Custom exceptions in `src/applescript/errors.py`
- Graceful handling of AppleScript execution failures
- Validation errors through Pydantic models
- Comprehensive logging for debugging AppleScript interactions