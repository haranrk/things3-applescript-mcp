# Code Style and Conventions

**Formatting**: Uses Ruff for both linting and formatting

**Type Hints**: Extensive use of Python type hints throughout the codebase

**Data Models**: Pydantic models for all data structures (Todo, Project, Area, Tag) with validation

**Naming Conventions**:
- Classes: PascalCase (e.g., `AppleScriptOrchestrator`, `Things3API`)
- Methods/Functions: snake_case (e.g., `get_todo`, `parse_date`)
- Private methods: Leading underscore (e.g., `_parse_todo`, `_execute_script`)
- Constants: UPPER_CASE for module-level constants

**Error Handling**: Custom exception classes (e.g., `AppleScriptError`)

**Logging**: Uses Python's logging module with module-level loggers

**Docstrings**: Module-level docstrings present, class and method docstrings should follow the pattern

**Import Organization**: Clear separation of stdlib, third-party, and local imports