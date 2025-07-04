# Claude Development Guidelines for things3-applescript-mcp

This document provides essential context and guidelines for AI assistants working on the Things 3 AppleScript MCP server project.

## Project Overview

This is a Python-based Model Context Protocol (MCP) server that provides bidirectional integration with Things 3, a popular macOS task management application. The server uses AppleScript to communicate with Things 3 and exposes its functionality through MCP tools.

## Architecture

The project follows a layered architecture:

1. **MCP Server Layer** (`src/mcp_server.py`): Exposes Things 3 functionality as MCP tools using FastMCP decorators
2. **API Layer** (`src/things3_api.py`): Provides high-level Python methods for Things 3 operations
3. **AppleScript Layer** (`src/applescript_orchestrator.py`): Handles AppleScript command construction, execution, and result parsing
4. **Data Models** (`src/models.py`): Pydantic models ensuring type safety for Todo, Project, Area, and Tag entities

## Development Setup

### Prerequisites
- Python 3.13 or higher
- macOS (required for AppleScript)
- Things 3 application installed
- uv package manager

### Installation
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Run tests
uv run pytest
```

### Running the Server
```bash
uv run fastmcp run src.mcp_server:app
```

## Code Style and Standards

### Python Code Style
- Use ruff for linting and formatting
- Run `uv run ruff check .` before committing
- Run `uv run ruff format .` to auto-format code
- Follow PEP 8 conventions

### Type Annotations
- Always use type hints for function parameters and return values
- Use Pydantic models for data validation
- Import types from `typing` module when needed

### Testing
- Write tests for all new functionality
- Place tests in `src/tests/` directory
- Use pytest fixtures for test data
- Mock AppleScript calls in tests using the fixture system

## Working with AppleScript

### Important Notes
1. AppleScript commands are platform-specific (macOS only)
2. The `applescript_orchestrator.py` handles all AppleScript execution
3. Results from AppleScript are parsed into Python dictionaries
4. Error handling is crucial as AppleScript can fail silently

### Adding New AppleScript Commands
1. Define the AppleScript template in the appropriate API method
2. Use the `AppleScriptOrchestrator` to execute commands
3. Parse results into appropriate Pydantic models
4. Add comprehensive error handling

## Common Tasks

### Adding a New MCP Tool
1. Define the tool in `mcp_server.py` using the `@app.tool` decorator
2. Implement the corresponding method in `things3_api.py`
3. Add AppleScript logic if needed in the API layer
4. Create appropriate Pydantic models in `models.py`
5. Write tests for the new functionality

### Modifying Existing Tools
1. Update the tool definition in `mcp_server.py`
2. Modify the API implementation
3. Update any affected models
4. Ensure backward compatibility when possible
5. Update tests accordingly

## Testing Guidelines

### Running Tests
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest src/tests/test_things3_api.py

# Run with coverage
uv run pytest --cov=src
```

### Test Structure
- Use descriptive test names that explain what is being tested
- Group related tests in classes
- Use fixtures for common test data
- Mock external dependencies (especially AppleScript calls)

## Error Handling

### AppleScript Errors
- Always wrap AppleScript execution in try-except blocks
- Log AppleScript errors with full context
- Return meaningful error messages to MCP clients

### Validation Errors
- Use Pydantic models for input validation
- Let Pydantic handle validation errors naturally
- Document expected formats in tool descriptions

## Performance Considerations

1. AppleScript calls can be slow - batch operations when possible
2. Cache frequently accessed data when appropriate
3. Use async operations where supported by FastMCP
4. Minimize the number of AppleScript calls per request

## Security Notes

1. Sanitize any user input before passing to AppleScript
2. Be cautious with dynamic AppleScript generation
3. Never expose system paths or sensitive information
4. Validate all input using Pydantic models

## Common Issues and Solutions

### Issue: AppleScript timeout
**Solution**: Increase timeout in AppleScriptOrchestrator or optimize the AppleScript query

### Issue: Things 3 not responding
**Solution**: Ensure Things 3 is running and accessible. Check system permissions for automation.

### Issue: Parsing AppleScript results fails
**Solution**: Check the fixture files for expected output format. Update parsing logic if Things 3 output format has changed.

## Contributing Guidelines

1. Create feature branches from `main`
2. Write comprehensive tests for new features
3. Update documentation as needed
4. Ensure all tests pass before submitting PR
5. Follow the existing code style and patterns

## Resources

- [MCP Documentation](https://modelcontextprotocol.io)
- [FastMCP Documentation](https://github.com/felixbrock/fastmcp)
- [Things 3 AppleScript Guide](https://culturedcode.com/things/support/articles/2803573/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

## Important Files

- `src/mcp_server.py` - Main server entry point and tool definitions
- `src/things3_api.py` - Core API implementation
- `src/applescript_orchestrator.py` - AppleScript execution layer
- `src/models.py` - Data models
- `pyproject.toml` - Project configuration and dependencies