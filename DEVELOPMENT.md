# Development Guide

This guide provides detailed instructions for setting up and developing the Things 3 AppleScript MCP server.

## Prerequisites

### System Requirements
- **macOS**: Required for AppleScript functionality
- **Python 3.13+**: The project uses modern Python features
- **Things 3**: Must be installed and accessible
- **Terminal access**: For running commands

### Required Permissions
Things 3 must have automation permissions enabled:
1. Open System Preferences → Security & Privacy → Privacy
2. Select "Automation" in the left sidebar
3. Ensure Terminal (or your terminal app) has permission to control Things 3

## Development Environment Setup

### 1. Install uv Package Manager

uv is a fast Python package manager that handles dependencies and virtual environments:

```bash
# macOS (using Homebrew)
brew install uv

# Or using the installer script
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and Setup Repository

```bash
# Clone the repository
git clone https://github.com/haranrk/things3-applescript-mcp.git
cd things3-applescript-mcp

# Create virtual environment and install dependencies
uv sync

# Verify installation
uv run python --version  # Should show Python 3.13+
```

### 3. IDE Setup

#### Visual Studio Code
1. Install Python extension
2. Select the interpreter: `Cmd+Shift+P` → "Python: Select Interpreter" → Choose `.venv/bin/python`
3. Install recommended extensions:
   - Python
   - Pylance
   - Ruff (for linting)

#### PyCharm
1. Open the project directory
2. Configure interpreter: Settings → Project → Python Interpreter → Add → Existing Environment
3. Select `.venv/bin/python`

## Running the Development Server

### Start the MCP Server
```bash
# Run in development mode with auto-reload
uv run fastmcp dev src.mcp_server:app

# Run in production mode
uv run fastmcp run src.mcp_server:app
```

### Testing with MCP Inspector
```bash
# Install MCP Inspector globally
npm install -g @modelcontextprotocol/inspector

# Run the inspector
mcp-inspector uv run fastmcp run src.mcp_server:app
```

## Testing

### Running Tests
```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest src/tests/test_things3_api.py

# Run specific test function
uv run pytest src/tests/test_things3_api.py::TestThings3API::test_get_all_todos

# Run with coverage report
uv run pytest --cov=src --cov-report=html
# Open htmlcov/index.html to view coverage report
```

### Writing Tests

#### Test Structure
```python
import pytest
from unittest.mock import Mock, patch
from src.things3_api import Things3API
from src.models import Todo

class TestThings3API:
    @pytest.fixture
    def api(self):
        """Create Things3API instance with mocked orchestrator."""
        orchestrator = Mock()
        return Things3API(orchestrator)
    
    def test_get_todo_success(self, api):
        """Test successful todo retrieval."""
        # Arrange
        api.orchestrator.execute.return_value = {
            "id": "123",
            "name": "Test Todo",
            "status": "open"
        }
        
        # Act
        result = api.get_todo("123")
        
        # Assert
        assert isinstance(result, Todo)
        assert result.id == "123"
        assert result.name == "Test Todo"
```

#### Using Fixtures
Test fixtures are stored in `src/tests/fixtures/` and contain sample AppleScript outputs:

```python
def test_parse_complex_output(self, api):
    """Test parsing complex AppleScript output."""
    with open("src/tests/fixtures/complex_todo.txt", "r") as f:
        sample_output = f.read()
    
    api.orchestrator.execute.return_value = eval(sample_output)
    result = api.get_all_todos()
    assert len(result) == 10
```

## Code Quality

### Linting and Formatting

The project uses Ruff for both linting and formatting:

```bash
# Check for linting issues
uv run ruff check .

# Fix auto-fixable issues
uv run ruff check . --fix

# Format code
uv run ruff format .

# Check without making changes
uv run ruff format . --check
```

### Pre-commit Checks

Before committing, always run:
```bash
# Run all quality checks
uv run ruff check . && uv run ruff format . && uv run pytest
```

### Type Checking

The project uses type hints extensively. While not enforced, you can run type checking:

```bash
# Install mypy (optional)
uv add --dev mypy

# Run type checking
uv run mypy src/
```

## Debugging

### Debug MCP Server

1. Add breakpoints in your code using `breakpoint()` or IDE breakpoints
2. Run the server in debug mode:
```bash
# Set debug environment variable
export FASTMCP_DEBUG=true

# Run with Python debugger
uv run python -m pdb -m fastmcp run src.mcp_server:app
```

### Debug AppleScript

To debug AppleScript commands:

1. Enable verbose logging in `applescript_orchestrator.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. Test AppleScript commands directly:
```bash
# In Python REPL
uv run python
>>> from src.applescript_orchestrator import AppleScriptOrchestrator
>>> orchestrator = AppleScriptOrchestrator()
>>> result = orchestrator.execute('tell application "Things3" to get name of to do id "YOUR_TODO_ID"')
>>> print(result)
```

### Common Issues

#### "Things 3 not responding"
- Ensure Things 3 is running
- Check automation permissions in System Preferences
- Try restarting Things 3

#### "Module not found" errors
- Ensure you're using `uv run` to execute commands
- Verify virtual environment is activated
- Run `uv sync` to ensure all dependencies are installed

#### AppleScript parsing errors
- Check the AppleScript syntax in Script Editor first
- Verify the expected output format matches parsing logic
- Use fixtures to test edge cases

## Making Changes

### Adding a New Tool

1. Define the tool in `src/mcp_server.py`:
```python
@app.tool
async def get_todos_by_date(date: str) -> list[dict]:
    """Get todos scheduled for a specific date."""
    api = Things3API()
    todos = api.get_todos_by_date(date)
    return [todo.model_dump() for todo in todos]
```

2. Implement the API method in `src/things3_api.py`:
```python
def get_todos_by_date(self, date: str) -> List[Todo]:
    """Get todos scheduled for a specific date."""
    script = f'''
    tell application "Things3"
        get to dos whose activation date is date "{date}"
    end tell
    '''
    result = self.orchestrator.execute(script)
    return [Todo(**todo_data) for todo_data in result]
```

3. Add tests in `src/tests/test_things3_api.py`
4. Update documentation

### Modifying Models

When changing data models in `src/models.py`:

1. Ensure backward compatibility when possible
2. Update all affected API methods
3. Update tests to reflect new model structure
4. Consider migration path for existing users

## Performance Optimization

### Profiling

```bash
# Profile the application
uv run python -m cProfile -o profile.stats -m fastmcp run src.mcp_server:app

# Analyze profile results
uv run python -m pstats profile.stats
```

### Optimization Tips

1. **Batch AppleScript calls**: Instead of multiple individual calls, combine into one script
2. **Cache frequently accessed data**: Implement caching for areas, tags, and projects
3. **Limit data fetching**: Use AppleScript filters instead of Python filtering
4. **Async operations**: Utilize FastMCP's async capabilities

## Release Process

1. Update version in `pyproject.toml`
2. Run full test suite: `uv run pytest`
3. Check code quality: `uv run ruff check . && uv run ruff format .`
4. Update CHANGELOG.md with release notes
5. Create git tag: `git tag -a v0.1.0 -m "Release version 0.1.0"`
6. Push tag: `git push origin v0.1.0`

## Getting Help

- Check existing issues on GitHub
- Read the [CLAUDE.md](CLAUDE.md) file for AI-specific guidelines
- Consult Things 3 AppleScript documentation
- Review MCP protocol specification

## Resources

### Documentation
- [Model Context Protocol](https://modelcontextprotocol.io)
- [FastMCP Documentation](https://github.com/felixbrock/fastmcp)
- [Things 3 AppleScript Guide](https://culturedcode.com/things/support/articles/2803573/)
- [uv Documentation](https://github.com/astral-sh/uv)

### Tools
- [Script Editor](https://support.apple.com/guide/script-editor/welcome/mac) - For testing AppleScript
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector) - For testing MCP tools
- [Pydantic Docs](https://docs.pydantic.dev/) - For data validation