# Suggested Commands

## Development Environment
```bash
# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate
```

## Running the Server
```bash
# Recommended - run as module
python -m src.mcp_server

# Alternative - run the package
python -m src
```

## Code Quality
```bash
# Lint code
ruff check src/

# Format code
ruff format src/
```

## Testing
```bash
# Run all tests
pytest

# Run specific test directory
pytest src/tests/

# Run specific test file with verbose output
pytest src/tests/test_applescript_orchestrator.py -v

# Run integration tests
python test_read_api.py
```

## System Commands (macOS)
```bash
# Basic file operations
ls, cd, mkdir, rm, cp, mv

# Search and grep
find, grep, rg (ripgrep if available)

# Git operations
git status, git add, git commit, git push, git pull

# Process management
ps, kill, jobs
```