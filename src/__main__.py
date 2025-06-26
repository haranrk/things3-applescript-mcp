"""Entry point for running the Things3 MCP server."""
from .mcp_server import mcp

if __name__ == "__main__":
    mcp.run()