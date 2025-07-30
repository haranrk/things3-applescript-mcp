# Project Overview

**Purpose**: This is an MCP (Model Control Protocol) server that bridges LLM clients with the Things 3 macOS application. It allows LLMs to read, update, and create todos, projects, areas, and tags in Things 3 through AppleScript integration.

**Architecture**: Layered approach with:
- MCP Server Handler (FastMCP-based)
- Things3 API Layer (Python interface)
- AppleScript Orchestrator (command execution)
- Data Models (Pydantic validation)

**Current Status**: Read operations fully implemented, write operations in progress.

**Requirements**: macOS with Things 3 app, Python 3.13+, AppleScript access.