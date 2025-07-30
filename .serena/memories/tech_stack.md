# Tech Stack

**Language**: Python 3.13+

**Package Manager**: uv (modern Python package manager)

**Key Dependencies**:
- `fastmcp>=2.8.1` - MCP server implementation
- `python-dateutil>=2.9.0.post0` - AppleScript date parsing

**Development Dependencies**:
- `pytest>=8.4.1` - Testing framework
- `ruff>=0.12.0` - Python linter and formatter

**Architecture Components**:
- FastMCP for MCP protocol implementation
- Pydantic for data models and validation
- AppleScript via `osascript` for Things 3 integration
- Standard library `subprocess` for command execution