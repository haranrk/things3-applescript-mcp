# Task Completion Checklist

When completing any coding task in this project:

## 1. Code Quality Checks
```bash
# Always run linting
ruff check src/

# Always run formatting
ruff format src/
```

## 2. Testing
```bash
# Run unit tests
pytest src/tests/

# For API changes, run integration tests
python test_read_api.py
```

## 3. Validation Steps
- Ensure all new code follows existing patterns and conventions
- Verify type hints are present and accurate
- Check that Pydantic models validate correctly
- Test AppleScript integration if relevant

## 4. Documentation
- Update docstrings for new/modified functions
- Update CLAUDE.md if architecture changes
- Ensure error handling follows existing patterns

## 5. Final Verification
- Server should start without errors: `python -m src.mcp_server`
- All tests should pass
- No linting errors should remain

**Note**: This project uses `uv` as package manager, not pip or poetry.