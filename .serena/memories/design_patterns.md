# Design Patterns and Guidelines

## Architecture Patterns
- **Layered Architecture**: Clear separation between MCP server, API layer, and AppleScript execution
- **Command Pattern**: AppleScript commands are encapsulated and executed through orchestrator
- **Factory Pattern**: Parser methods create appropriate model instances from AppleScript data

## Error Handling
- Custom exception hierarchy with `AppleScriptError`
- Graceful handling of AppleScript failures
- Validation errors through Pydantic models

## Data Flow
- **Inbound**: MCP Client → Server → API → Orchestrator → Things 3
- **Outbound**: Things 3 → AppleScript → Parsing → Pydantic Models → MCP Response
- **Conversion**: Python objects ↔ AppleScript values via orchestrator methods

## Key Guidelines
- Always use Pydantic models for data validation
- Parse AppleScript dates using `python-dateutil`
- Handle missing/optional values gracefully (use `None` defaults)
- Use logging for debugging AppleScript execution
- Maintain backward compatibility in API changes
- Follow the existing async/await patterns in FastMCP tools

## Testing Strategy
- Unit tests with mocked AppleScript calls
- Integration tests against real Things 3 app
- Fixture-based testing with real AppleScript output samples