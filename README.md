# Things 3 AppleScript MCP Server

A Model Context Protocol (MCP) server that provides integration with Things 3 task management application on macOS through AppleScript.

## Features

- **Full Things 3 Integration**: Access and manipulate todos, projects, areas, and tags
- **MCP Protocol**: Standards-based integration using the Model Context Protocol
- **Type-Safe**: Comprehensive type hints and Pydantic models for data validation
- **Well-Tested**: Includes test suite with fixtures for reliable development

## Available MCP Tools

### Todo Operations
- `get_todo` - Retrieve a specific todo by ID
- `get_all_todos` - Fetch all todos from Things 3
- `get_todos_by_list` - Get todos from specific lists (Inbox, Today, Upcoming, etc.)
- `get_todos_by_project` - Retrieve todos belonging to a specific project
- `get_todos_by_area` - Fetch todos from a specific area
- `get_todos_by_tag` - Get todos with a specific tag
- `create_todo` - Create new todos with various properties

### Project Operations
- `get_project` - Retrieve a specific project by ID
- `get_all_projects` - Fetch all projects
- `get_projects_by_area` - Get projects belonging to a specific area

### Area Operations
- `get_area` - Retrieve a specific area by ID
- `get_all_areas` - Fetch all areas

### Tag Operations
- `get_tag` - Retrieve a specific tag by ID
- `get_all_tags` - Fetch all tags

## Installation

### Prerequisites

- macOS (required for AppleScript)
- Python 3.13 or higher
- Things 3 application installed
- uv package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/haranrk/things3-applescript-mcp.git
cd things3-applescript-mcp
```

2. Install uv (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Install dependencies:
```bash
uv sync
```

## Usage

### Running the MCP Server

```bash
uv run fastmcp run src.mcp_server:app
```

### Using with Claude Desktop

Add the following to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "things3": {
      "command": "uv",
      "args": ["run", "fastmcp", "run", "src.mcp_server:app"],
      "cwd": "/path/to/things3-applescript-mcp"
    }
  }
}
```

### Example Usage

Once connected, you can use natural language to interact with Things 3:

- "Show me all my todos for today"
- "Create a new todo to review pull requests"
- "What projects do I have in my Work area?"
- "Show me all todos tagged with 'urgent'"

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src

# Run specific test file
uv run pytest src/tests/test_things3_api.py
```

### Code Quality

```bash
# Run linter
uv run ruff check .

# Format code
uv run ruff format .
```

### Project Structure

```
src/
├── mcp_server.py              # MCP server and tool definitions
├── things3_api.py             # High-level Things 3 API
├── applescript_orchestrator.py # AppleScript execution layer
├── models.py                  # Pydantic data models
└── tests/                     # Test suite with fixtures
```

## Architecture

The project follows a clean, layered architecture:

1. **MCP Layer**: Handles protocol communication and tool definitions
2. **API Layer**: Provides high-level Python interface to Things 3
3. **AppleScript Layer**: Manages AppleScript command execution
4. **Model Layer**: Ensures type safety with Pydantic models

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and ensure they pass
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

Please read [CLAUDE.md](CLAUDE.md) for detailed development guidelines.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [FastMCP](https://github.com/felixbrock/fastmcp)
- Integrates with [Things 3](https://culturedcode.com/things/) by Cultured Code
- Uses [Model Context Protocol](https://modelcontextprotocol.io) specification